"""
Puts a job's vector into the job index and takes it out again.

The text that is embedded is built by JobTextBuilder, the same builder the
recruiter-side matching uses, so a job has one representation whichever way
it is searched.
"""

from typing import Any, Optional

from loguru import logger

from app.database.mongodb.id_generator import next_faiss_id
from app.matching.embedding_text import JobTextBuilder
from app.vector_store.job_vector_store import JobVectorStore


class JobIndexer:

    def __init__(
        self,
        embedding_service: Optional[Any] = None,
        vector_store: Optional[JobVectorStore] = None,
        text_builder: Optional[JobTextBuilder] = None,
    ) -> None:
        self._embedding_service = embedding_service
        self.vector_store = vector_store or JobVectorStore()
        self.text_builder = text_builder or JobTextBuilder()

    @property
    def embedding_service(self) -> Any:
        # Loaded on first use: the embedding model is large.
        if self._embedding_service is None:
            from app.embeddings.services.embedding_service import EmbeddingService

            self._embedding_service = EmbeddingService()

        return self._embedding_service

    def embed(self, job: Any) -> Any:
        return self.embedding_service.generate_embedding(self.text_builder.text(job))

    def index(self, database: Any, job: Any) -> int:
        """Embeds the job, stores its vector and returns the faiss id used."""

        faiss_id = next_faiss_id(database)

        self.vector_store.add(faiss_id, self.embed(job))

        logger.info("Indexed a job under faiss id {}.", faiss_id)

        return faiss_id

    def remove(self, faiss_id: Optional[int]) -> None:
        if faiss_id is None:
            return

        self.vector_store.remove(faiss_id)
