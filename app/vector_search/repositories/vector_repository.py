from abc import ABC, abstractmethod
from typing import List

from app.vector_search.models.vector_record import VectorRecord


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
        vector,
        top_k: int = 5,
    ) -> List[VectorRecord]:
        pass


    @abstractmethod
    def delete(
        self,
        vector_id: str,
    ) -> None:
        pass