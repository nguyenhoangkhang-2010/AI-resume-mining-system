from abc import ABC, abstractmethod
from typing import List

from app.vector_search.models.vector_record import (
    VectorRecord,
)

from app.vector_search.models.vector_search_result import (
    VectorSearchResult,
)


class VectorRepository(ABC):
    """
    Abstract vector storage contract.

    Implementations:
    - FAISS
    - Milvus
    - Qdrant
    - Pinecone
    """


    @abstractmethod
    def add(
        self,
        record: VectorRecord,
    ) -> None:
        pass


    @abstractmethod
    def search(
        self,
        query_vector,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        pass


    @abstractmethod
    def delete(
        self,
        vector_id: str,
    ) -> None:
        pass