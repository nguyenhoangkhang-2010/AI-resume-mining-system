import numpy as np
import pytest

from app.database.vector_db.faiss_manager import FaissManager
from app.models.candidate import CandidateModel, Experience
from app.services.candidate_reindex_service import CandidateReindexService


class FakeEmbeddingService:
    def __init__(self):
        self.texts = None
        self.batch_size = None

    def generate_batch_embeddings(self, texts, batch_size=32):
        self.texts = list(texts)
        self.batch_size = batch_size

        return np.eye(len(texts), 4, dtype=np.float32)


class FakeVectorStore:
    def __init__(self):
        self.replaced = None

    def replace_all(self, faiss_ids, embeddings):
        self.replaced = (list(faiss_ids), embeddings)


def candidate(faiss_id, skills):
    return CandidateModel(
        resume_id=f"r{faiss_id}",
        faiss_id=faiss_id,
        skills=skills,
        normalized_skills=skills,
        experience=[Experience(role="Engineer")],
    )


def test_reindex_rebuilds_from_profile_text():
    embeddings = FakeEmbeddingService()
    store = FakeVectorStore()

    count = CandidateReindexService(embeddings, store, batch_size=8).reindex(
        [candidate(10, ["python"]), candidate(20, ["java"])]
    )

    assert count == 2
    assert embeddings.batch_size == 8
    assert embeddings.texts == [
        "Engineer python",
        "Engineer java",
    ]
    assert store.replaced[0] == [10, 20]


def test_reindex_rejects_duplicate_faiss_ids():
    service = CandidateReindexService(FakeEmbeddingService(), FakeVectorStore())

    with pytest.raises(ValueError):
        service.reindex([candidate(1, ["a"]), candidate(1, ["b"])])


def test_reindex_of_nothing_empties_the_index():
    store = FakeVectorStore()

    count = CandidateReindexService(FakeEmbeddingService(), store).reindex([])

    assert count == 0
    assert store.replaced == ([], [])


# ------------------------------------------------------------ FAISS manager


@pytest.fixture
def manager(tmp_path):
    instance = FaissManager.__new__(FaissManager)
    instance.index_path = tmp_path / "candidate.index"
    instance.dimension = 4
    instance._load_or_create_index()

    return instance


def test_replace_all_replaces_contents_and_persists(manager):
    manager.add_vector(1, np.array([1, 0, 0, 0], dtype=np.float32))

    manager.replace_all(
        np.array([7, 8]),
        np.array([[0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32),
    )

    scores, ids = manager.search(np.array([0, 1, 0, 0], dtype=np.float32), 2)

    assert ids[0] == 7
    assert 1 not in ids.tolist()
    assert manager.index_path.exists()
    assert not manager.index_path.with_suffix(".tmp").exists()


def test_replace_all_validates_input(manager):
    with pytest.raises(ValueError):
        manager.replace_all(np.array([1, 1]), np.zeros((2, 4), dtype=np.float32))

    with pytest.raises(ValueError):
        manager.replace_all(np.array([1]), np.zeros((2, 4), dtype=np.float32))
