from app.vector_search.services.vector_search_service import (
    VectorSearchService,
)

from app.vector_search.repositories.faiss_vector_repository import (
    FaissVectorRepository,
)


class VectorSearchFactory:


    @staticmethod
    def create() -> VectorSearchService:

        repository = FaissVectorRepository()

        return VectorSearchService(
            repository
        )