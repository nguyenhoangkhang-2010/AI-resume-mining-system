from app.vector_search.factory.vector_search_factory import (
    VectorSearchFactory,
)

from app.vector_search.services.vector_search_service import (
    VectorSearchService,
)


def test_vector_search_factory():

    service = VectorSearchFactory.create()

    assert isinstance(
        service,
        VectorSearchService
    )