from app.vector_search.repositories.vector_repository import (
    VectorRepository
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
    ):

        return self.repository.search(
            query_vector,
            top_k
        )