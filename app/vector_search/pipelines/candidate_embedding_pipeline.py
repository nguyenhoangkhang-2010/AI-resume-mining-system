from app.embeddings.services.embedding_service import (
    EmbeddingService,
)

from app.vector_search.models.vector_record import (
    VectorRecord,
)

from app.vector_search.repositories.vector_repository import (
    VectorRepository,
)


class CandidateEmbeddingPipeline:


    def __init__(
        self,
        embedding_service: EmbeddingService,
        repository: VectorRepository,
    ):
        self.embedding_service = embedding_service
        self.repository = repository


    def index_candidate(
        self,
        candidate_id: str,
        text: str,
        metadata: dict,
    ) -> VectorRecord:


        embedding = self.embedding_service.generate_embedding(
            text
        )


        record = VectorRecord(
            id=candidate_id,
            vector=embedding,
            entity_type="candidate",
            metadata=metadata,
        )


        self.repository.add(
            record
        )


        return record