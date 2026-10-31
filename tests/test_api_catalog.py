from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_candidate_search_service,
    get_candidate_service,
    get_job_service,
    get_recommendation_service,
    get_resume_catalog_service,
)
from app.database.mongodb.connection import mongo_db
from app.main import app
from app.schemas.recommendation_schema import (
    RecommendationItem,
    RecommendationResponse,
)
from app.services.candidate_search_service import CandidateSearchService
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.services.recommendation_service import RecommendationService
from app.services.resume_catalog_service import ResumeCatalogService
from tests.fakes.fake_mongo import FakeCollection

BASE = datetime(2026, 1, 1)


def oid():
    return ObjectId()


class FakeDb(dict):
    pass


@pytest.fixture
def database(monkeypatch):
    db = FakeDb(
        resumes=FakeCollection(),
        candidates=FakeCollection(),
        jobs=FakeCollection(),
    )

    monkeypatch.setattr(mongo_db, "get_db", lambda: db)

    return db


@pytest.fixture
def client():
    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


class RecordingVectorStore:
    def __init__(self, found=None):
        self.removed = []
        self.found = found or []
        self.queries = []

    def remove_candidate_embedding(self, faiss_id):
        self.removed.append(faiss_id)
        return True

    def search_similar_candidates(self, embedding, top_k):
        self.queries.append(top_k)
        return self.found


def resume_doc(index, status="processed", **extra):
    return {
        "_id": oid(),
        "filename": f"cv-{index}.pdf",
        "file_path": f"/srv/data/uploads/secret-{index}.pdf",
        "upload_status": status,
        "created_at": BASE + timedelta(minutes=index),
        "extracted_data": {"raw_text": "private"},
        **extra,
    }


def candidate_doc(index, resume_id="r", skills=None, faiss_id=None, **extra):
    return {
        "_id": oid(),
        "resume_id": resume_id,
        "faiss_id": faiss_id if faiss_id is not None else index,
        "personal_info": {"full_name": f"Person {index}", "email": f"p{index}@example.com"},
        "skills": skills or ["Python", "SQL"],
        "normalized_skills": skills or ["python", "sql"],
        "experience": [{"role": "Engineer"}],
        "created_at": BASE + timedelta(minutes=index),
        **extra,
    }


# ------------------------------------------------------------- resumes


def use_catalog(database, upload_dir, vector_store=None):
    store = vector_store or RecordingVectorStore()

    app.dependency_overrides[get_resume_catalog_service] = lambda: ResumeCatalogService(
        store, upload_dir
    )

    return store


def test_resume_list_is_newest_first_and_paginated(database, client, tmp_path):
    use_catalog(database, tmp_path)
    database["resumes"].documents = [resume_doc(i) for i in range(5)]

    response = client.get("/api/v1/resumes/?limit=2&offset=1")

    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 5
    assert (body["limit"], body["offset"]) == (2, 1)
    assert [item["filename"] for item in body["items"]] == ["cv-3.pdf", "cv-2.pdf"]


def test_resume_list_hides_paths_and_extracted_text(database, client, tmp_path):
    use_catalog(database, tmp_path)
    database["resumes"].documents = [resume_doc(1)]

    item = client.get("/api/v1/resumes/").json()["items"][0]

    assert set(item) == {
        "id", "filename", "status", "reason", "warnings", "confidence", "created_at"
    }
    assert "secret" not in str(item)


def test_resume_list_filters_by_status(database, client, tmp_path):
    use_catalog(database, tmp_path)
    database["resumes"].documents = [
        resume_doc(1, "processed"),
        resume_doc(2, "needs_review", status_reason="no_text_extracted"),
        resume_doc(3, "failed"),
    ]

    body = client.get("/api/v1/resumes/?status=needs_review").json()

    assert body["total"] == 1
    assert body["items"][0]["reason"] == "no_text_extracted"


def test_resume_list_rejects_unknown_status_and_bad_paging(database, client, tmp_path):
    use_catalog(database, tmp_path)

    assert client.get("/api/v1/resumes/?status=bogus").status_code == 422
    assert client.get("/api/v1/resumes/?limit=0").status_code == 422
    assert client.get("/api/v1/resumes/?limit=101").status_code == 422
    assert client.get("/api/v1/resumes/?offset=-1").status_code == 422


def test_unknown_stored_status_is_reported_as_pending(database, client, tmp_path):
    use_catalog(database, tmp_path)
    database["resumes"].documents = [resume_doc(1, "legacy-status")]

    assert client.get("/api/v1/resumes/").json()["items"][0]["status"] == "pending"


def test_resume_detail_includes_the_candidate_id(database, client, tmp_path):
    use_catalog(database, tmp_path)
    resume = resume_doc(1)
    candidate = candidate_doc(1, resume_id=str(resume["_id"]))
    database["resumes"].documents = [resume]
    database["candidates"].documents = [candidate]

    body = client.get(f"/api/v1/resumes/{resume['_id']}").json()

    assert body["id"] == str(resume["_id"])
    assert body["candidate_id"] == str(candidate["_id"])


def test_confidence_is_shown_in_the_list_the_detail_and_the_status(database, client, tmp_path):
    use_catalog(database, tmp_path)
    confidence = {
        "score": 0.62,
        "level": "medium",
        "components": {"completeness": 0.8},
        "sections": {"experience": 0.9},
        "reasons": ["read_by_ocr"],
    }
    resume = resume_doc(1, confidence=confidence)
    database["resumes"].documents = [resume, resume_doc(2)]

    items = client.get("/api/v1/resumes/").json()["items"]
    by_name = {item["filename"]: item for item in items}

    assert by_name["cv-1.pdf"]["confidence"]["score"] == 0.62
    assert by_name["cv-1.pdf"]["confidence"]["reasons"] == ["read_by_ocr"]
    assert by_name["cv-2.pdf"]["confidence"] is None

    detail = client.get(f"/api/v1/resumes/{resume['_id']}").json()
    status = client.get(f"/api/v1/resumes/{resume['_id']}/status").json()

    assert detail["confidence"]["level"] == "medium"
    assert status["confidence"]["level"] == "medium"


def test_a_malformed_stored_confidence_is_left_out(database, client, tmp_path):
    use_catalog(database, tmp_path)
    resume = resume_doc(1, confidence={"score": "high"})
    database["resumes"].documents = [resume]

    assert client.get(f"/api/v1/resumes/{resume['_id']}").json()["confidence"] is None


def test_resume_detail_without_candidate(database, client, tmp_path):
    use_catalog(database, tmp_path)
    resume = resume_doc(1, "needs_review", status_reason="no_text_extracted")
    database["resumes"].documents = [resume]

    body = client.get(f"/api/v1/resumes/{resume['_id']}").json()

    assert body["candidate_id"] is None
    assert body["status"] == "needs_review"


@pytest.mark.parametrize("identifier", [str(ObjectId()), "not-an-object-id"])
def test_unknown_or_malformed_resume_id_is_404(database, client, tmp_path, identifier):
    use_catalog(database, tmp_path)

    for suffix in ("", "/status"):
        response = client.get(f"/api/v1/resumes/{identifier}{suffix}")

        assert response.status_code == 404
        assert response.json()["code"] == "not_found"

    assert client.delete(f"/api/v1/resumes/{identifier}").status_code == 404


def test_deleting_a_resume_removes_candidate_vector_and_file(database, client, tmp_path):
    upload = tmp_path / "cv.pdf"
    upload.write_bytes(b"%PDF-1.7")

    resume = resume_doc(1, file_path=str(upload))
    candidate = candidate_doc(1, resume_id=str(resume["_id"]), faiss_id=42)
    other = candidate_doc(2, resume_id="another-resume", faiss_id=43)

    database["resumes"].documents = [resume]
    database["candidates"].documents = [candidate, other]

    store = use_catalog(database, tmp_path)

    response = client.delete(f"/api/v1/resumes/{resume['_id']}")

    assert response.status_code == 204
    assert database["resumes"].documents == []
    assert database["candidates"].documents == [other]
    assert store.removed == [42]
    assert not upload.exists()


def test_deleting_a_resume_that_is_processing_is_a_conflict(database, client, tmp_path):
    resume = resume_doc(1, "processing")
    database["resumes"].documents = [resume]
    use_catalog(database, tmp_path)

    response = client.delete(f"/api/v1/resumes/{resume['_id']}")

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert len(database["resumes"].documents) == 1


def test_files_outside_the_upload_directory_are_never_deleted(database, client, tmp_path):
    outside = tmp_path / "elsewhere" / "important.txt"
    outside.parent.mkdir()
    outside.write_text("keep")

    uploads = tmp_path / "uploads"
    uploads.mkdir()

    resume = resume_doc(1, file_path=str(outside))
    database["resumes"].documents = [resume]
    use_catalog(database, uploads)

    assert client.delete(f"/api/v1/resumes/{resume['_id']}").status_code == 204
    assert outside.exists()


# ---------------------------------------------------------------- jobs


def make_job_service():
    service = JobService.__new__(JobService)

    return service


def job_doc(index, **extra):
    return {
        "_id": oid(),
        "title": f"Job {index}",
        "description": "d",
        "raw_text": "d",
        "required_skills": ["python"],
        "normalized_skills": ["python"],
        "experience_years": 3,
        "created_at": BASE + timedelta(minutes=index),
        "updated_at": BASE,
        **extra,
    }


@pytest.fixture
def jobs(database, monkeypatch, client):
    collection = FakeCollection()
    monkeypatch.setattr(JobService, "jobs_col", property(lambda self: collection))
    app.dependency_overrides[get_job_service] = make_job_service

    return collection


def test_job_list_is_paginated_and_summarised(jobs, client):
    jobs.documents = [job_doc(i) for i in range(3)]

    body = client.get("/api/v1/jobs/?limit=2").json()

    assert body["total"] == 3
    assert [j["title"] for j in body["items"]] == ["Job 2", "Job 1"]
    assert set(body["items"][0]) == {
        "id", "title", "occupation", "location", "required_skills", "experience_years",
        "created_at",
    }


def test_job_detail_matches_the_create_response_shape(jobs, client):
    job = job_doc(1, occupation="Software Developers")
    jobs.documents = [job]

    body = client.get(f"/api/v1/jobs/{job['_id']}").json()

    assert body["_id"] == str(job["_id"])
    assert body["title"] == "Job 1"
    assert body["occupation"] == "Software Developers"


def test_job_delete(jobs, client):
    job = job_doc(1)
    jobs.documents = [job]

    assert client.delete(f"/api/v1/jobs/{job['_id']}").status_code == 204
    assert jobs.documents == []
    assert client.delete(f"/api/v1/jobs/{job['_id']}").status_code == 404


@pytest.mark.parametrize("identifier", [str(ObjectId()), "bad-id"])
def test_unknown_job_is_404(jobs, client, identifier):
    assert client.get(f"/api/v1/jobs/{identifier}").status_code == 404


# ---------------------------------------------------------- candidates


@pytest.fixture
def candidates(database, client):
    app.dependency_overrides[get_candidate_service] = CandidateService

    return database["candidates"]


def test_candidate_list_summaries_hide_contact_details(candidates, client):
    candidates.documents = [candidate_doc(1)]

    item = client.get("/api/v1/candidates/").json()["items"][0]

    assert item["full_name"] == "Person 1"
    assert item["skills"] == ["python", "sql"]
    assert item["skill_count"] == 2
    assert "email" not in str(item)


def test_candidate_list_limits_skills_to_ten(candidates, client):
    candidates.documents = [candidate_doc(1, skills=[f"skill{i}" for i in range(25)])]

    item = client.get("/api/v1/candidates/").json()["items"][0]

    assert len(item["skills"]) == 10
    assert item["skill_count"] == 25


def test_candidate_skill_filter_ignores_case(candidates, client):
    candidates.documents = [
        candidate_doc(1, skills=["python"]),
        candidate_doc(2, skills=["java"]),
    ]

    body = client.get("/api/v1/candidates/?skill=Python").json()

    assert body["total"] == 1
    assert body["items"][0]["full_name"] == "Person 1"


def test_candidate_detail_returns_the_full_profile(candidates, client):
    document = candidate_doc(1)
    candidates.documents = [document]

    body = client.get(f"/api/v1/candidates/{document['_id']}").json()

    assert body["personal_info"]["email"] == "p1@example.com"
    assert body["skills"] == ["Python", "SQL"]


@pytest.mark.parametrize("identifier", [str(ObjectId()), "bad-id"])
def test_unknown_candidate_is_404(candidates, client, identifier):
    assert client.get(f"/api/v1/candidates/{identifier}").status_code == 404


# -------------------------------------------------------------- search


class FakeEmbeddings:
    def __init__(self):
        self.texts = []

    def generate_embedding(self, text):
        self.texts.append(text)
        return [0.1, 0.2]


def test_search_returns_candidates_sorted_by_scaled_score(database, client):
    first = candidate_doc(1, faiss_id=1)
    second = candidate_doc(2, faiss_id=2)
    database["candidates"].documents = [first, second]

    store = RecordingVectorStore(
        found=[
            {"faiss_id": 1, "similarity_score": 0.5},
            {"faiss_id": 2, "similarity_score": 0.9},
            {"faiss_id": 3, "similarity_score": 0.8},
        ]
    )
    embeddings = FakeEmbeddings()
    app.dependency_overrides[get_candidate_search_service] = lambda: CandidateSearchService(
        embeddings, store
    )

    body = client.post(
        "/api/v1/search/candidates", json={"query": "python developer", "top_k": 5}
    ).json()

    assert embeddings.texts == ["python developer"]
    assert store.queries == [5]
    assert [hit["score"] for hit in body["results"]] == [90.0, 50.0]
    assert body["results"][0]["candidate"]["full_name"] == "Person 2"
    assert "email" not in str(body)


def test_search_with_no_matches_returns_an_empty_list(database, client):
    app.dependency_overrides[get_candidate_search_service] = lambda: CandidateSearchService(
        FakeEmbeddings(), RecordingVectorStore()
    )

    body = client.post("/api/v1/search/candidates", json={"query": "anything"}).json()

    assert body == {"query": "anything", "results": []}


@pytest.mark.parametrize(
    "payload",
    [{}, {"query": ""}, {"query": "x" * 1001}, {"query": "x", "top_k": 0}, {"query": "x", "top_k": 51}],
)
def test_search_validates_the_request(database, client, payload):
    app.dependency_overrides[get_candidate_search_service] = lambda: CandidateSearchService(
        FakeEmbeddings(), RecordingVectorStore()
    )

    assert client.post("/api/v1/search/candidates", json=payload).status_code == 422


# ----------------------------------------------------- recommendations


class FakeEngine:
    def __init__(self, items):
        self.items = items
        self.calls = []

    def recommend(self, required, owned):
        self.calls.append((required, owned))

        return RecommendationResponse(recommendations=self.items)


def use_recommendations(engine):
    app.dependency_overrides[get_recommendation_service] = lambda: RecommendationService(engine)


def test_recommendations_list_missing_skills_and_deduplicate(database, client):
    job = job_doc(1, required_skills=["python", "docker", "sql"],
                  normalized_skills=["python", "docker", "sql"])
    candidate = candidate_doc(1, skills=["python"])
    database["jobs"].documents = [job]
    database["candidates"].documents = [candidate]

    engine = FakeEngine(
        [
            RecommendationItem(type="course", title="Learn Docker", priority="medium", source="STATIC"),
            RecommendationItem(type="skill", title="SQL", priority="medium", source="ESCO"),
            RecommendationItem(type="skill", title="sql", priority="medium", source="ESCO"),
        ]
    )
    use_recommendations(engine)

    body = client.get(
        f"/api/v1/recommendations/?job_id={job['_id']}&candidate_id={candidate['_id']}"
    ).json()

    assert body["missing_skills"] == ["docker", "sql"]
    assert [r["title"] for r in body["recommendations"]] == ["Learn Docker", "SQL"]
    assert engine.calls[0][0] == ["python", "docker", "sql"]


def test_no_missing_skills_means_no_recommendations(database, client):
    job = job_doc(1)
    candidate = candidate_doc(1)
    database["jobs"].documents = [job]
    database["candidates"].documents = [candidate]

    engine = FakeEngine([])
    use_recommendations(engine)

    body = client.get(
        f"/api/v1/recommendations/?job_id={job['_id']}&candidate_id={candidate['_id']}"
    ).json()

    assert body["missing_skills"] == []
    assert body["recommendations"] == []
    assert engine.calls == []


def test_recommendations_need_existing_job_and_candidate(database, client):
    job = job_doc(1)
    candidate = candidate_doc(1)
    database["jobs"].documents = [job]
    database["candidates"].documents = [candidate]
    use_recommendations(FakeEngine([]))

    unknown = ObjectId()

    assert client.get(
        f"/api/v1/recommendations/?job_id={unknown}&candidate_id={candidate['_id']}"
    ).status_code == 404
    assert client.get(
        f"/api/v1/recommendations/?job_id={job['_id']}&candidate_id=bad"
    ).status_code == 404
    assert client.get("/api/v1/recommendations/").status_code == 422


# ---------------------------------------------------------------- docs


def test_openapi_lists_every_resource(client):
    paths = client.get("/openapi.json").json()["paths"]

    expected = {
        "/api/v1/resumes/": {"get"},
        "/api/v1/resumes/upload": {"post"},
        "/api/v1/resumes/{resume_id}": {"get", "delete"},
        "/api/v1/resumes/{resume_id}/status": {"get"},
        "/api/v1/jobs/": {"get", "post"},
        "/api/v1/jobs/{job_id}": {"get", "delete"},
        "/api/v1/candidates/": {"get"},
        "/api/v1/candidates/{candidate_id}": {"get"},
        "/api/v1/matches/{job_id}": {"get"},
        "/api/v1/search/candidates": {"post"},
        "/api/v1/recommendations/": {"get"},
    }

    for path, methods in expected.items():
        assert path in paths, path
        assert methods <= set(paths[path]), path
