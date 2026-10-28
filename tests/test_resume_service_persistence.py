from types import SimpleNamespace

import pytest
from bson import ObjectId

from app.matching.embedding_text import CandidateTextBuilder
from app.models.candidate import CandidateModel
from app.services.resume_service import ResumeService


class RecordingVectorStore:
    def __init__(self, add_result=True):
        self.add_result = add_result
        self.removed = []

    def add_candidate_embedding(self, faiss_id, embedding):
        return self.add_result

    def remove_candidate_embedding(self, faiss_id):
        self.removed.append(faiss_id)
        return True


class FakeCandidates:
    def __init__(self, previous=None, fail=False):
        self.previous = previous
        self.fail = fail
        self.inserted = []
        self.replaced = []

    def find_one(self, query, projection=None):
        return self.previous

    def insert_one(self, document):
        if self.fail:
            raise RuntimeError("write failed")

        self.inserted.append(document)

        return SimpleNamespace(inserted_id=ObjectId())

    def replace_one(self, query, document):
        if self.fail:
            raise RuntimeError("write failed")

        self.replaced.append((query, document))


def make_service(monkeypatch, collection):
    monkeypatch.setattr(
        ResumeService, "candidates_col", property(lambda self: collection)
    )

    service = ResumeService.__new__(ResumeService)
    service.vector_store = RecordingVectorStore()

    return service


def candidate(faiss_id):
    return CandidateModel(resume_id="resume-1", faiss_id=faiss_id)


def test_new_candidate_is_inserted(monkeypatch):
    collection = FakeCandidates()
    service = make_service(monkeypatch, collection)

    candidate_id = service._save_candidate(candidate(10))

    assert collection.inserted[0]["faiss_id"] == 10
    assert ObjectId.is_valid(candidate_id)
    assert service.vector_store.removed == []


def test_reprocessing_replaces_candidate_and_drops_old_vector(monkeypatch):
    previous_id = ObjectId()
    collection = FakeCandidates(previous={"_id": previous_id, "faiss_id": 3})
    service = make_service(monkeypatch, collection)

    candidate_id = service._save_candidate(candidate(10))

    assert candidate_id == str(previous_id)
    assert collection.inserted == []
    assert collection.replaced[0][0] == {"_id": previous_id}
    assert service.vector_store.removed == [3]


def test_reprocessing_with_same_faiss_id_keeps_vector(monkeypatch):
    collection = FakeCandidates(previous={"_id": ObjectId(), "faiss_id": 10})
    service = make_service(monkeypatch, collection)

    service._save_candidate(candidate(10))

    assert service.vector_store.removed == []


def test_failed_write_removes_the_new_vector(monkeypatch):
    service = make_service(monkeypatch, FakeCandidates(fail=True))

    with pytest.raises(RuntimeError, match="write failed"):
        service._save_candidate(candidate(10))

    assert service.vector_store.removed == [10]


def test_failed_replace_keeps_the_old_vector(monkeypatch):
    collection = FakeCandidates(
        previous={"_id": ObjectId(), "faiss_id": 3}, fail=True
    )
    service = make_service(monkeypatch, collection)

    with pytest.raises(RuntimeError):
        service._save_candidate(candidate(10))

    # only the vector that was just added is discarded
    assert service.vector_store.removed == [10]


def test_faiss_id_comes_from_the_counter(monkeypatch):
    seen = {}

    def fake_next(db):
        seen["db"] = db
        return 42

    monkeypatch.setattr("app.services.resume_service.next_faiss_id", fake_next)
    monkeypatch.setattr(ResumeService, "db", property(lambda self: "the-db"))

    service = ResumeService.__new__(ResumeService)

    assert service._generate_faiss_id() == 42
    assert seen["db"] == "the-db"


def test_failed_vector_add_raises():
    class Embeddings:
        def generate_embedding(self, text):
            return [1.0]

    class Normalizer:
        def normalize(self, skill):
            return skill

    service = ResumeService.__new__(ResumeService)
    service.vector_store = RecordingVectorStore(add_result=False)
    service.embedding_service = Embeddings()
    service.skill_normalizer = Normalizer()
    service.candidate_text_builder = CandidateTextBuilder()
    service._generate_faiss_id = lambda: 1

    with pytest.raises(RuntimeError, match="vector index"):
        service._build_candidate("resume-1", {"skills": ["python"]})
