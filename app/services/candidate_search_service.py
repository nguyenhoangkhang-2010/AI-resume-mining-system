from typing import Any, Dict, List

from app.database.mongodb.connection import mongo_db
from app.schemas.search_schema import CandidateSearchHit, CandidateSearchResponse
from app.services.candidate_service import summarize

# Cosine similarity is reported on a 0-100 scale, like the match scores.
SCORE_SCALE = 100


class CandidateSearchService:
    """Free-text semantic search over indexed candidates."""

    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    @property
    def candidates_col(self):
        return mongo_db.get_db()["candidates"]

    def search(self, query: str, top_k: int) -> CandidateSearchResponse:
        embedding = self.embedding_service.generate_embedding(query)

        found = self.vector_store.search_similar_candidates(embedding, top_k=top_k)

        if not found:
            return CandidateSearchResponse(query=query, results=[])

        scores = {item["faiss_id"]: item["similarity_score"] for item in found}

        documents: Dict[int, Dict[str, Any]] = {
            document["faiss_id"]: document
            for document in self.candidates_col.find({"faiss_id": {"$in": list(scores)}})
        }

        hits: List[CandidateSearchHit] = [
            CandidateSearchHit(
                candidate=summarize(documents[faiss_id]),
                score=round(max(0.0, min(1.0, scores[faiss_id])) * SCORE_SCALE, 2),
            )
            for faiss_id in scores
            if faiss_id in documents
        ]

        hits.sort(key=lambda hit: hit.score, reverse=True)

        return CandidateSearchResponse(query=query, results=hits)
