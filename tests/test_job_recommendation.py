from types import SimpleNamespace

import numpy as np
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import get_job_recommendation_service
from app.core.config.settings import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.database.vector_db.faiss_manager import FaissManager
from app.main import app
from app.schemas.job_schema import JobCreateRequest
from app.services.job_indexer import JobIndexer
from app.services.job_recommendation_service import JobRecommendationService
from app.services.job_reindex_service import JobReindexService
from app.services.job_service import JobService
from app.vector_store import job_vector_store
from app.vector_store.job_vector_store import JobVectorStore, shared_manager
from tests.fakes.fake_mongo import FakeCollection

DIMENSION = 4
# Cosine 0.3 between the two job families, 0.0 with anything else: the index
# drops hits with no similarity at all, so unrelated texts must still overlap.
CODE = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
CARE = np.array([0.3, 0.95, 0.0, 0.0], dtype=np.float32)
OTHER = np.array([0.1, 0.1, 0.9, 0.0], dtype=np.float32)


class FakeEmbedding:
    """Python/nursing texts get orthogonal vectors; anything else a third one."""

    def generate_embedding(self, text):
        lowered = text.lower()

        if "python" in lowered or "backend" in lowered:
            return CODE

        if "nurs" in lowered or "ward" in lowered:
            return CARE

        return OTHER

    def generate_batch_embeddings(self, texts):
        return np.array([self.generate_embedding(text) for text in texts])


class CounterCollection:
    def __init__(self):
        self.seq = 0

    def find_one_and_update(self, query, update, upsert=False, return_document=None):
        self.seq += 1

        return {"_id": query["_id"], "seq": self.seq}


class IdCollection(FakeCollection):
    def insert_one(self, document):
        self.documents.append({"_id": ObjectId(), **document})

        return SimpleNamespace(inserted_id=self.documents[-1]["_id"])

    def update_one(self, query, update):
        for document in self._select(query):
            document.update(update["$set"])


class FakeDatabase(dict):
    def __missing__(self, name):
        self[name] = IdCollection()

        return self[name]


@pytest.fixture
def database(monkeypatch):
    db = FakeDatabase(counters=CounterCollection())

    for service in (JobRecommendationService, JobService):
        monkeypatch.setattr(service, "db", property(lambda self: db))

    return db


@pytest.fixture
def store(tmp_path):
    return JobVectorStore(FaissManager.for_path(tmp_path / "job.index", dimension=DIMENSION))


def add_job(db, store, title, skills, faiss_id, location=None, years=None, text_vector=None):
    object_id = ObjectId()
    db["jobs"].documents.append(
        {
            "_id": object_id,
            "title": title,
            "description": title,
            "required_skills": skills,
            "normalized_skills": skills,
            "location": location,
            "experience_years": years,
            "faiss_id": faiss_id,
        }
    )

    if faiss_id is not None:
        store.add(faiss_id, text_vector if text_vector is not None else FakeEmbedding().generate_embedding(title))

    return str(object_id)


def add_candidate(db, skills, summary="Python backend engineer", resume_id="r1"):
    object_id = ObjectId()
    db["candidates"].documents.append(
        {
            "_id": object_id,
            "resume_id": resume_id,
            "skills": skills,
            "normalized_skills": skills,
            "summary": summary,
            "faiss_id": 1,
        }
    )

    return str(object_id)


def service(store):
    return JobRecommendationService(embedding_service=FakeEmbedding(), job_vector_store=store)


# ------------------------------------------------------------ recommending


def test_jobs_come_best_first_with_the_reasons(database, store):
    add_job(database, store, "Nurse on a ward", ["wound care", "triage"], 1)
    code = add_job(database, store, "Backend engineer", ["python", "sql"], 2)
    candidate = add_candidate(database, ["python", "sql", "docker"])

    result = service(store).recommend_for_candidate(candidate, min_score=0)

    assert result.results[0].job_id == code
    assert result.results[0].score > result.results[1].score
    top = result.results[0]
    assert top.score_breakdown.matched_skills == ["python", "sql"]
    assert top.skill_gaps == []
    assert result.results[1].skill_gaps == ["wound care", "triage"]
    assert top.score_breakdown.skill_score == 100


def test_weak_matches_are_left_out_by_default(database, store):
    add_job(database, store, "Nurse on a ward", ["wound care"], 1)
    add_job(database, store, "Backend engineer", ["python"], 2)
    candidate = add_candidate(database, ["python"])

    result = service(store).recommend_for_candidate(candidate)

    assert [match.title for match in result.results] == ["Backend engineer"]
    assert result.metadata.min_score == 50
    assert result.metadata.below_min_score == 1


def test_a_candidate_chooses_how_low_to_look(database, store):
    add_job(database, store, "Nurse on a ward", ["wound care"], 1)
    add_job(database, store, "Backend engineer", ["python"], 2)
    candidate = add_candidate(database, ["python"])

    result = service(store).recommend_for_candidate(candidate, min_score=0)

    assert len(result.results) == 2
    assert result.metadata.below_min_score == 0


def test_the_location_filter_ignores_case_and_matches_part_of_the_text(database, store):
    add_job(database, store, "Backend engineer", ["python"], 1, location="Ho Chi Minh City")
    add_job(database, store, "Backend developer", ["python"], 2, location="Hanoi")
    add_job(database, store, "Backend engineer II", ["python"], 3, location=None)
    candidate = add_candidate(database, ["python"])

    result = service(store).recommend_for_candidate(candidate, location=" hanoi ")

    assert [match.location for match in result.results] == ["Hanoi"]
    assert result.metadata.outside_location == 2


def test_only_top_k_jobs_are_returned(database, store):
    for number in range(5):
        add_job(database, store, f"Backend engineer {number}", ["python"], number + 1)

    result = service(store).recommend_for_candidate(add_candidate(database, ["python"]), top_k=2)

    assert len(result.results) == 2
    assert result.metadata.ranked == 2


def test_jobs_without_a_vector_are_reported_not_hidden(database, store):
    add_job(database, store, "Backend engineer", ["python"], 1)
    add_job(database, store, "Old job", ["python"], None)

    result = service(store).recommend_for_candidate(add_candidate(database, ["python"]))

    assert result.metadata.unindexed_jobs == 1
    assert [match.title for match in result.results] == ["Backend engineer"]


def test_experience_counts_when_the_job_asks_for_it(database, store):
    senior = add_job(database, store, "Backend engineer", ["python"], 1, years=10)
    candidate = add_candidate(database, ["python"])
    database["candidates"].documents[0]["experience"] = [
        {"role": "Dev", "company": "X", "start_date": "2024", "end_date": "2025"}
    ]

    result = service(store).recommend_for_candidate(candidate, min_score=0)

    assert result.results[0].job_id == senior
    assert result.results[0].score_breakdown.experience_score < 50


def test_an_empty_job_index_gives_an_empty_list(database, store):
    result = service(store).recommend_for_candidate(add_candidate(database, ["python"]))

    assert result.results == []
    assert result.metadata.retrieved == 0


def test_unknown_and_malformed_candidates_are_not_found(database, store):
    with pytest.raises(NotFoundError):
        service(store).recommend_for_candidate(str(ObjectId()))

    with pytest.raises(NotFoundError):
        service(store).recommend_for_candidate("not-an-id")


def test_from_a_resume(database, store):
    add_job(database, store, "Backend engineer", ["python"], 1)
    resume_id = ObjectId()
    database["resumes"].documents.append({"_id": resume_id})
    candidate = add_candidate(database, ["python"], resume_id=str(resume_id))

    result = service(store).recommend_for_resume(str(resume_id))

    assert result.candidate_id == candidate
    assert len(result.results) == 1


def test_a_resume_without_a_profile_is_a_conflict_and_an_unknown_one_not_found(database, store):
    resume_id = ObjectId()
    database["resumes"].documents.append({"_id": resume_id})

    with pytest.raises(ConflictError):
        service(store).recommend_for_resume(str(resume_id))

    with pytest.raises(NotFoundError):
        service(store).recommend_for_resume(str(ObjectId()))


# ----------------------------------------------------------- the job index


def test_the_job_index_finds_the_closest_job_and_forgets_removed_ones(store):
    store.add(10, CODE)
    store.add(20, CARE)

    assert [hit["faiss_id"] for hit in store.search(CODE, 5)][0] == 10

    assert store.remove(10) is True
    assert 10 not in store.indexed_ids()
    assert store.remove(999) is False


def test_one_manager_is_shared_per_index_file(tmp_path, monkeypatch):
    monkeypatch.setattr(job_vector_store, "_managers", {})
    monkeypatch.setattr(settings, "FAISS_SAVE_EVERY", 1)

    first = shared_manager(tmp_path / "a.index")

    assert shared_manager(tmp_path / "a.index") is first
    assert shared_manager(tmp_path / "b.index") is not first


# --------------------------------------------------------------- job service


def job_service(indexer):
    class Pipeline:
        def process(self, source):
            return {"skills": ["Python"], "responsibilities": "- build apis"}

    class Normalizer:
        def normalize(self, skill):
            return skill.lower()

    class Matcher:
        def find(self, text):
            return None

    return JobService(Pipeline(), Normalizer(), Matcher(), job_indexer=indexer)


@pytest.fixture
def job_database(database):
    return database


def test_a_new_job_gets_a_vector_and_remembers_its_id(job_database, store):
    indexer = JobIndexer(FakeEmbedding(), store)
    created = job_service(indexer).create_job(
        JobCreateRequest(title="Backend engineer", description="Python APIs", location=" Hanoi ")
    )

    stored = job_database["jobs"].documents[0]

    assert stored["faiss_id"] in store.indexed_ids()
    assert created.location == "Hanoi"
    assert stored["location"] == "Hanoi"


def test_a_job_is_saved_even_when_indexing_fails(job_database, store):
    class Broken(JobIndexer):
        def index(self, database, job):
            raise RuntimeError("embedding model unavailable")

    created = job_service(Broken(FakeEmbedding(), store)).create_job(
        JobCreateRequest(title="Backend engineer", description="Python APIs")
    )

    assert created.id
    assert len(job_database["jobs"].documents) == 1
    assert job_database["jobs"].documents[0].get("faiss_id") is None


def test_deleting_a_job_removes_its_vector(job_database, store):
    indexer = JobIndexer(FakeEmbedding(), store)
    service_ = job_service(indexer)
    created = service_.create_job(JobCreateRequest(title="Backend engineer", description="Python APIs"))

    service_.delete_job(created.id)

    assert store.indexed_ids() == set()


def test_without_an_indexer_and_with_indexing_off_nothing_is_indexed(job_database):
    service_ = job_service(None)

    service_.create_job(JobCreateRequest(title="Backend engineer", description="Python APIs"))

    assert service_.job_indexer is None


# ------------------------------------------------------------------ reindex


def test_reindex_gives_every_job_a_vector_and_drops_stale_ones(database, store):
    kept = add_job(database, store, "Backend engineer", ["python"], 7)
    add_job(database, store, "Nurse on a ward", ["triage"], None)
    store.add(99, OTHER)  # a vector whose job no longer exists

    count = JobReindexService(database, FakeEmbedding(), store).reindex()

    ids = {doc["faiss_id"] for doc in database["jobs"].documents}

    assert count == 2
    assert None not in ids and 7 in ids
    assert store.indexed_ids() == ids
    assert kept


def test_reindex_of_an_empty_collection_empties_the_index(database, store):
    store.add(5, CODE)

    assert JobReindexService(database, FakeEmbedding(), store).reindex() == 0
    assert store.indexed_ids() == set()


# ---------------------------------------------------------------------- API


class StubRecommender:
    def __init__(self):
        self.calls = []

    def _response(self):
        from app.schemas.job_match_schema import JobMatchMetadata, JobMatchResponse

        return JobMatchResponse(
            candidate_id="c1",
            results=[],
            metadata=JobMatchMetadata(
                retrieved=0, ranked=0, below_min_score=0, outside_location=0,
                unindexed_jobs=0, min_score=50,
            ),
        )

    def recommend_for_candidate(self, candidate_id, top_k=10, min_score=None, location=None):
        self.calls.append(("candidate", candidate_id, top_k, min_score, location))

        return self._response()

    def recommend_for_resume(self, resume_id, **options):
        self.calls.append(("resume", resume_id, options))

        if resume_id == "pending":
            raise ConflictError("not yet")

        return self._response()


@pytest.fixture
def api():
    stub = StubRecommender()
    app.dependency_overrides[get_job_recommendation_service] = lambda: stub

    yield TestClient(app, raise_server_exceptions=False), stub

    app.dependency_overrides.clear()


def test_the_candidate_endpoint_passes_its_options_on(api):
    client, stub = api

    response = client.get("/api/v1/candidates/c1/jobs?top_k=5&min_score=40&location=Hanoi")

    assert response.status_code == 200
    assert response.json()["metadata"]["unindexed_jobs"] == 0
    assert stub.calls == [("candidate", "c1", 5, 40.0, "Hanoi")]


def test_the_defaults_leave_the_service_to_decide(api):
    client, stub = api

    client.get("/api/v1/candidates/c1/jobs")

    assert stub.calls == [("candidate", "c1", 10, None, None)]


@pytest.mark.parametrize("query", ["top_k=0", "top_k=51", "min_score=101", "min_score=-1", "location=" + "x" * 121])
def test_out_of_range_options_are_rejected(api, query):
    client, stub = api

    assert client.get(f"/api/v1/candidates/c1/jobs?{query}").status_code == 422
    assert stub.calls == []


def test_the_resume_endpoint_reports_an_unprocessed_resume_as_409(api):
    client, _ = api

    assert client.get("/api/v1/resumes/r1/jobs").status_code == 200

    response = client.get("/api/v1/resumes/pending/jobs")

    assert response.status_code == 409 and response.json()["code"] == "conflict"


def test_the_endpoints_need_a_key_when_authentication_is_on(api, monkeypatch):
    client, stub = api
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEYS", "user:" + "k" * 32)

    assert client.get("/api/v1/candidates/c1/jobs").status_code == 401
    assert client.get("/api/v1/candidates/c1/jobs", headers={"X-API-Key": "k" * 32}).status_code == 200
