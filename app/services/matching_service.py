from bson import ObjectId
from loguru import logger
from typing import List

from app.database.mongodb.connection import mongo_db
from app.models.job import JobModel
from app.models.candidate import CandidateModel
from app.schemas.matching_schema import MatchResponse
from app.embeddings.services.embedding_service import EmbeddingService
from app.vector_store.vector_store import VectorStore
from app.matching.ranking.ranking_engine import RankingEngine


class MatchingService:    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.ranking_engine = RankingEngine()

    @property
    def db(self):
        return mongo_db.get_db()
        
    @property
    def jobs_col(self):
        return self.db["jobs"]
        
    @property
    def candidates_col(self):
        return self.db["candidates"]

    def match_candidates_for_job(self, job_id: str) -> MatchResponse:
        logger.info(f"Orchestrating matching process for Job ID: {job_id}")
        
        job = self._get_job(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")
            
        job_context = job.description + " " + " ".join(job.required_skills)
        job_embedding = self.embedding_service.generate_embedding(job_context)
        
        faiss_results = self.vector_store.search_similar_candidates(job_embedding)
        if not faiss_results:
            logger.warning("No suitable candidates found in Vector Store.")
            return MatchResponse(job_id=job_id, results=[])
            
        faiss_ids = [res["faiss_id"] for res in faiss_results]
        candidates = self._get_candidates_by_faiss_ids(faiss_ids)
        
        match_response = self.ranking_engine.rank_candidates(
            job=job,
            candidates=candidates,
            faiss_results=faiss_results
        )
        
        return match_response

    def _get_job(self, job_id: str) -> JobModel | None:
        data = self.jobs_col.find_one({"_id": ObjectId(job_id)})
        return JobModel(**{**data, "_id": str(data["_id"])}) if data else None
        
    def _get_candidates_by_faiss_ids(self, faiss_ids: List[int]) -> List[CandidateModel]:
        cursor = self.candidates_col.find({"faiss_id": {"$in": faiss_ids}})
        return [CandidateModel(**{**doc, "_id": str(doc["_id"])}) for doc in cursor]