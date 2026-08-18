from typing import List

from app.vector_search.models.vector_record import (
    VectorRecord,
)

from app.vector_search.models.vector_search_result import (
    VectorSearchResult,
)

from app.vector_search.repositories.vector_repository import (
    VectorRepository,
)

from app.database.vector_db.faiss_manager import (
    FaissManager,
)


class FaissVectorRepository(VectorRepository):
    """
    FAISS implementation of VectorRepository.
    """


    def __init__(self):
        self.faiss_manager = FaissManager()


    def add(
        self,
        record: VectorRecord,
    ) -> None:
        faiss_id = hash(record.id)
        self.faiss_manager.add_vector(
            faiss_id,
            record.vector,
        )


    def search(
        self,
        query_vector,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        distances, indices = self.faiss_manager.search(
            query_vector,
            top_k,
        )
        results = []
        for score, faiss_id in zip(
            distances,
            indices,
        ):
            if faiss_id == -1:
                continue
            results.append(
                VectorSearchResult(
                    id=str(faiss_id),
                    score=float(score),
                    entity_type="unknown",
                    metadata={},
                )
            )
        return results


    def delete(
        self,
        vector_id: str,
    ) -> None:

        raise NotImplementedError(
            "FAISS delete will be implemented later"
        )