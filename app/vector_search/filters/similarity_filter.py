from typing import List

from app.vector_search.models.vector_search_result import (
    VectorSearchResult,
)


class SimilarityFilter:

    def __init__(
        self,
        threshold: float = 0.5,
    ):
        self.threshold = threshold


    def filter(
        self,
        results: List[VectorSearchResult],
    ) -> List[VectorSearchResult]:

        return [
            result
            for result in results
            if result.score >= self.threshold
        ]