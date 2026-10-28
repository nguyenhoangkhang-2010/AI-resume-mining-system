import pytest

from app.models.candidate import CandidateModel
from app.services.index_consistency_service import (
    ConsistencyReport,
    IndexConsistencyService,
)


class FakeStore:
    def __init__(self, ids):
        self.ids = set(ids)
        self.added = []
        self.flushed = False

    def indexed_ids(self):
        return set(self.ids)

    def remove_candidate_embedding(self, faiss_id):
        self.ids.discard(faiss_id)
        return True

    def add_candidate_embedding(self, faiss_id, embedding):
        self.ids.add(faiss_id)
        self.added.append(faiss_id)
        return True

    def flush(self):
        self.flushed = True


class FakeEmbeddings:
    def generate_embedding(self, text):
        return [1.0]


def candidate(faiss_id, resume_id=None):
    return CandidateModel(
        resume_id=resume_id or f"r{faiss_id}",
        faiss_id=faiss_id,
        skills=["python"],
    )


def test_consistent_state_is_ok():
    report = IndexConsistencyService(FakeStore({1, 2})).check(
        [candidate(1), candidate(2)]
    )

    assert report.ok


def test_check_finds_missing_orphans_and_duplicates():
    store = FakeStore({1, 9})

    report = IndexConsistencyService(store).check(
        [candidate(1), candidate(2), candidate(2, "r2b")]
    )

    assert report.missing_in_index == [2]
    assert report.orphan_vectors == [9]
    assert report.duplicate_faiss_ids == [2]
    assert not report.ok


def test_repair_removes_orphans_and_re_adds_missing():
    store = FakeStore({1, 9})
    service = IndexConsistencyService(store, FakeEmbeddings())

    result = service.repair([candidate(1), candidate(3)])

    assert result == {"removed_orphans": 1, "added_missing": 1}
    assert store.ids == {1, 3}
    assert store.flushed


def test_repair_leaves_duplicate_ids_alone():
    store = FakeStore(set())
    service = IndexConsistencyService(store, FakeEmbeddings())

    result = service.repair([candidate(2), candidate(2, "r2b")])

    assert result["added_missing"] == 0
    assert store.added == []


def test_repair_needs_embeddings_only_for_missing_vectors():
    orphan_only = IndexConsistencyService(FakeStore({1, 9}))

    assert orphan_only.repair([candidate(1)])["removed_orphans"] == 1

    with pytest.raises(ValueError):
        IndexConsistencyService(FakeStore(set())).repair([candidate(1)])


def test_empty_report_is_ok():
    assert ConsistencyReport().ok
