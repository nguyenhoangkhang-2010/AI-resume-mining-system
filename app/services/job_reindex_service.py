"""
Rebuilds the job index from the jobs stored in MongoDB.

MongoDB is the source of truth: the index is replaced by one vector per stored
job, jobs that had no vector get one, and vectors of jobs that no longer exist
disappear. Run it for jobs created before the job index existed, after the
embedding text changes, or when the index file was lost.
"""

from typing import Any, List

from app.database.mongodb.id_generator import next_faiss_id
from app.matching.embedding_text import JobTextBuilder
from app.models.job import JobModel
from app.vector_store.job_vector_store import JobVectorStore


class JobReindexService:

    def __init__(
        self,
        database: Any,
        embedding_service: Any,
        vector_store: JobVectorStore,
        text_builder: JobTextBuilder | None = None,
    ) -> None:
        self.database = database
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.text_builder = text_builder or JobTextBuilder()

    def reindex(self) -> int:
        collection = self.database["jobs"]
        documents = list(collection.find({}))

        if not documents:
            self.vector_store.replace_all([], self._empty())
            return 0

        ids: List[int] = []
        texts: List[str] = []

        for document in documents:
            faiss_id = document.get("faiss_id")

            if faiss_id is None:
                faiss_id = next_faiss_id(self.database)
                collection.update_one(
                    {"_id": document["_id"]}, {"$set": {"faiss_id": faiss_id}}
                )

            job = JobModel(**{**document, "_id": str(document["_id"])})
            ids.append(int(faiss_id))
            texts.append(self.text_builder.text(job))

        vectors = self.embedding_service.generate_batch_embeddings(texts)
        self.vector_store.replace_all(ids, vectors)

        return len(ids)

    @staticmethod
    def _empty() -> Any:
        import numpy as np

        from app.core.constants.app_constants import EMBEDDING_DIMENSION

        return np.zeros((0, EMBEDDING_DIMENSION), dtype=np.float32)
