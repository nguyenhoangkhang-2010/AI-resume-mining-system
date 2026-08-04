from typing import List

from app.vector_search.repositories.vector_repository import (
    VectorRepository
)

from app.vector_search.models.vector_search_result import (
    VectorSearchResult
)


class VectorSearchService:


    def __init__(
        self,
        repository: VectorRepository,
    ):
        self.repository = repository



    def search(
        self,
        query_vector,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        if query_vector is None:
            raise ValueError(
                "Query vector cannot be None"
            )
        records = self.repository.search(
            query_vector,
            top_k
        )
        return [
            VectorSearchResult(
                id=record.id,
                score=record.metadata.get(
                    "similarity_score",
                    0.0
                ),
                entity_type=record.entity_type,
                metadata=record.metadata,
            )
            for record in records
        ]