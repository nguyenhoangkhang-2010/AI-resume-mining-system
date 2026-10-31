"""
Integration tests against a real MongoDB.

They run only with `pytest -m integration` and are skipped when no server
answers on MONGO_URI. Every test uses a throwaway database whose name starts
with `ai_resume_it_`; it is dropped afterwards and the configured
application database is never touched.
"""

import threading

import numpy as np
import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import connection as connection_module
from app.database.mongodb.id_generator import next_faiss_id
from app.database.mongodb.indexes import INDEXES
from app.database.vector_db.faiss_manager import FaissManager
from app.matching.embedding_text import CandidateTextBuilder
from app.models.candidate import CandidateModel
from app.services.index_consistency_service import IndexConsistencyService
from app.services.resume_service import ResumeService
from app.vector_store.vector_store import VectorStore


pytestmark = pytest.mark.integration

DIMENSION = 8


def unit(position):
    vector = np.zeros(DIMENSION, dtype=np.float32)
    vector[position % DIMENSION] = 1.0
    return vector


def candidate_document(faiss_id, resume_id):
    candidate = CandidateModel(
        resume_id=resume_id,
        faiss_id=faiss_id,
        skills=["python"],
        normalized_skills=["python"],
    )

    return candidate.model_dump(by_alias=True, exclude={"id"})


def test_connect_creates_declared_indexes(database):
    for collection, specs in INDEXES.items():
        existing = database[collection].index_information()

        for spec in specs:
            assert spec["name"] in existing, (collection, spec["name"])

            if spec.get("unique"):
                assert existing[spec["name"]].get("unique") is True


def test_ping_reflects_a_live_connection(database):
    assert connection_module.mongo_db.ping() is True


def test_faiss_id_counter_is_unique_under_concurrency(database):
    ids = []
    lock = threading.Lock()

    def worker():
        batch = [next_faiss_id(database) for _ in range(25)]

        with lock:
            ids.extend(batch)

    threads = [threading.Thread(target=worker) for _ in range(8)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(ids) == 200
    assert sorted(ids) == list(range(1, 201))


def test_unique_indexes_reject_duplicate_candidates(database):
    candidates = database["candidates"]

    candidates.insert_one(candidate_document(1, "resume-a"))

    with pytest.raises(DuplicateKeyError):
        candidates.insert_one(candidate_document(1, "resume-b"))

    with pytest.raises(DuplicateKeyError):
        candidates.insert_one(candidate_document(2, "resume-a"))


def make_resume_service(tmp_path):
    service = ResumeService.__new__(ResumeService)
    service.vector_store = VectorStore.__new__(VectorStore)
    service.vector_store.faiss_manager = FaissManager.for_path(
        tmp_path / "candidate.index", dimension=DIMENSION
    )

    return service


def test_reprocessing_a_resume_keeps_one_candidate_and_one_vector(
    database, tmp_path
):
    service = make_resume_service(tmp_path)
    store = service.vector_store

    first = CandidateModel(resume_id="resume-1", faiss_id=1, skills=["python"])
    store.add_candidate_embedding(1, unit(0))
    first_id = service._save_candidate(first)

    second = CandidateModel(resume_id="resume-1", faiss_id=2, skills=["java"])
    store.add_candidate_embedding(2, unit(1))
    second_id = service._save_candidate(second)

    documents = list(database["candidates"].find({}))

    assert first_id == second_id
    assert len(documents) == 1
    assert documents[0]["faiss_id"] == 2
    assert documents[0]["skills"] == ["java"]
    assert store.indexed_ids() == {2}


def test_failed_write_leaves_no_orphan_vector(database, tmp_path):
    service = make_resume_service(tmp_path)
    store = service.vector_store

    database["candidates"].insert_one(candidate_document(1, "resume-1"))

    clash = CandidateModel(resume_id="resume-other", faiss_id=1)
    store.add_candidate_embedding(1, unit(0))
    store.add_candidate_embedding(1, unit(1))

    with pytest.raises(DuplicateKeyError):
        service._save_candidate(clash)

    # the compensation removed the vector that had just been added
    assert store.indexed_ids() == set()


def test_consistency_check_against_real_collection(database, tmp_path):
    manager = FaissManager.for_path(
        tmp_path / "candidate.index", dimension=DIMENSION
    )
    store = VectorStore.__new__(VectorStore)
    store.faiss_manager = manager

    database["candidates"].insert_many(
        [candidate_document(1, "r1"), candidate_document(2, "r2")]
    )

    manager.add_vector(1, unit(0))
    manager.add_vector(99, unit(5))

    candidates = [
        CandidateModel(**{**doc, "_id": str(doc["_id"])})
        for doc in database["candidates"].find({})
    ]

    report = IndexConsistencyService(store).check(candidates)

    assert report.missing_in_index == [2]
    assert report.orphan_vectors == [99]

    class Embeddings:
        def generate_embedding(self, text):
            return unit(2)

    result = IndexConsistencyService(store, Embeddings()).repair(candidates)

    assert result == {"removed_orphans": 1, "added_missing": 1}
    assert IndexConsistencyService(store).check(candidates).ok


def test_legacy_string_experience_description_round_trips(database):
    """
    Older documents stored an experience description as one string; they
    must still load as candidates.
    """

    legacy = candidate_document(7, "legacy")
    legacy["experience"] = [
        {
            "role": "Engineer",
            "company": "Acme",
            "start_date": "2020",
            "end_date": "2022",
            "description": "Built and shipped things.",
            "total_years_extracted": 2,
        }
    ]

    inserted = database["candidates"].insert_one(legacy).inserted_id

    document = database["candidates"].find_one({"_id": ObjectId(inserted)})

    candidate = CandidateModel(**{**document, "_id": str(document["_id"])})

    assert candidate.experience[0].description == ["Built and shipped things."]
    assert "Built and shipped things." in CandidateTextBuilder().text(candidate)
