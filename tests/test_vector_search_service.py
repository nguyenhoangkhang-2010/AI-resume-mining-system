import numpy as np

from app.vector_search.services.vector_search_service import (
    VectorSearchService,
)

from app.vector_search.models.vector_search_result import (
    VectorSearchResult,
)


class FakeRepository:


    def search(
        self,
        query_vector,
        top_k,
    ):

        return [
            VectorSearchResult(
                id="candidate_1",
                score=0.92,
                entity_type="candidate",
                metadata={}
            )
        ]



def test_vector_search_service():

    service = VectorSearchService(
        FakeRepository()
    )

    results = service.search(
        np.array([0.1]),
        top_k=5
    )


    assert len(results) == 1

    assert results[0].score == 0.92