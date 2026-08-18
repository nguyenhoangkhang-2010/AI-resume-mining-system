import numpy as np

from app.vector_search.services.vector_search_service import (
    VectorSearchService,
)

from app.vector_search.models.vector_record import (
    VectorRecord,
)


class FakeRepository:


    def search(
        self,
        query_vector,
        top_k,
    ):

        return [
            VectorRecord(
                id="candidate_1",
                vector=None,
                entity_type="candidate",
                metadata={
                    "similarity_score": 0.92
                }
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

    assert results[0].entity_type == "candidate"