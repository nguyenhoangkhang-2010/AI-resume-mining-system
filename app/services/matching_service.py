from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger
from typing import List

from app.core.exceptions import NotFoundError
from app.database.mongodb.connection import mongo_db

from app.models.job import JobModel
from app.models.candidate import CandidateModel

from app.schemas.matching_schema import MatchResponse
from app.schemas.ranking_schema import RankingMetadata

from app.embeddings.services.embedding_service import EmbeddingService

from app.vector_store.vector_store import VectorStore

from app.core.constants.app_constants import EMBEDDING_VERSION
from app.matching.embedding_text import JobTextBuilder
from app.core.config.settings import settings
from app.matching.ranking.candidate_scorer import HybridCandidateScorer
from app.matching.reranking.cross_encoder_reranker import build_reranker
from app.matching.ranking.ranking_config import RankingConfig
from app.matching.ranking.ranking_pipeline import RankingPipeline


class MatchingService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.job_text_builder = JobTextBuilder()
        self.ranking_config = RankingConfig()
        self.ranking_pipeline = RankingPipeline(
            candidate_scorer=HybridCandidateScorer(),
            reranker=(
                build_reranker(
                    settings.RERANKER_MODEL,
                    settings.RERANKER_TOP_N,
                    settings.RERANKER_WEIGHT,
                )
                if settings.RERANKER_ENABLED
                else None
            ),
        )
        
    @property
    def db(self):
        return mongo_db.get_db()
    @property
    def jobs_col(self):
        return self.db["jobs"]
    @property
    def candidates_col(self):
        return self.db["candidates"]


    def match_candidates_for_job(
        self,
        job_id: str
    ) -> MatchResponse:
        logger.info(
            f"Matching candidates for job {job_id}"
        )
        job = self._get_job(job_id)
        if not job:
            raise NotFoundError(
                f"Job not found: {job_id}"
            )
        embedding = (
            self.embedding_service
            .generate_embedding(
                self.job_text_builder.text(job)
            )
        )
        faiss_results = (
            self.vector_store
            .search_similar_candidates(
                embedding,
                top_k=self.ranking_config.retrieval_top_k
            )
        )
        if not faiss_results:
            return MatchResponse(
                job_id=job_id,
                results=[],
                metadata=RankingMetadata(
                    total_candidates=0,
                    ranked_candidates=0,
                    filtered_candidates=0,
                    similarity_threshold=0,
                )
            )
        faiss_ids = [
            item["faiss_id"]
            for item in faiss_results
        ]
        candidates = (
            self._get_candidates_by_faiss_ids(
                faiss_ids
            )
        )
        stale = [
            candidate
            for candidate in candidates
            if candidate.embedding_version != EMBEDDING_VERSION
        ]
        if stale:
            logger.warning(
                f"{len(stale)} of {len(candidates)} candidates were indexed "
                f"with an older embedding version; run "
                f"scripts/reindex_candidates.py to rebuild the index."
            )
        score_map = {
            item["faiss_id"]:
            item["similarity_score"]
            for item in faiss_results
        }
        ranking_result = (
            self.ranking_pipeline.process(
                job=job,
                candidates=candidates,
                score_map=score_map
            )
        )
        return MatchResponse(
            job_id=job_id,
            results=ranking_result.results,
            metadata=ranking_result.metadata
        )


    def _get_job(
        self,
        job_id:str
    ):
        try:
            object_id = ObjectId(job_id)
        except (InvalidId, TypeError):
            return None

        data = self.jobs_col.find_one(
            {
                "_id":object_id
            }
        )
        if not data:
            return None
        data["_id"] = str(
            data["_id"]
        )
        return JobModel(**data)


    def _get_candidates_by_faiss_ids(
        self,
        faiss_ids:List[int]
    ):
        cursor = self.candidates_col.find(
            {
                "faiss_id":{
                    "$in":faiss_ids
                }
            }
        )
        return [
            CandidateModel(
                **{
                    **doc,
                    "_id":str(doc["_id"])
                }
            )
            for doc in cursor
        ]