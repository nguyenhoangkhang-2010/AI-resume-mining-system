from app.vector_search.repositories.faiss_vector_repository import (
    FaissVectorRepository,
)


def test_faiss_repository_implements_interface():

    repository = FaissVectorRepository()

    assert repository is not None