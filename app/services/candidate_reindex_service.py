from typing import Sequence

from loguru import logger

from app.matching.embedding_text import CandidateTextBuilder
from app.models.candidate import CandidateModel


class CandidateReindexService:
    """
    Rebuilds the vector index from stored candidates, using the current
    embedding text. Needed whenever the text builders change, because old
    vectors would no longer be comparable with new job embeddings.
    """

    def __init__(
        self,
        embedding_service,
        vector_store,
        text_builder: CandidateTextBuilder | None = None,
        batch_size: int = 64,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.text_builder = text_builder or CandidateTextBuilder()
        self.batch_size = batch_size

    def reindex(self, candidates: Sequence[CandidateModel]) -> int:
        faiss_ids = [candidate.faiss_id for candidate in candidates]

        if len(set(faiss_ids)) != len(faiss_ids):
            raise ValueError("Candidates contain duplicate faiss ids")

        if not candidates:
            self.vector_store.replace_all([], [])
            return 0

        texts = [self.text_builder.text(c) for c in candidates]

        logger.info(f"Embedding {len(texts)} candidates for reindexing.")

        embeddings = self.embedding_service.generate_batch_embeddings(
            texts,
            batch_size=self.batch_size,
        )

        self.vector_store.replace_all(faiss_ids, embeddings)

        return len(candidates)
