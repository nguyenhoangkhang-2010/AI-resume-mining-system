from app.vector_search.repositories.vector_repository import (
    VectorRepository
)


def test_vector_repository_contract():

    assert VectorRepository.__abstractmethods__ == {
        "add",
        "search",
        "delete",
    }