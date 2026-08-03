from typing import List, Dict, Any
from loguru import logger

from app.matching.ranking.ranking_config import (
    RankingConfig,
)
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.matching_schema import MatchResponse
from app.matching.ranking.ranking_adapter import RankingAdapter
from app.matching.ranking.ranking_sorter import RankingSorter
from app.matching.ranking.ranking_pipeline import RankingPipeline


class RankingEngine:
    
    def __init__(
        self,
        ranking_adapter=None,
        config=None,
        ranking_sorter=None,
        ranking_pipeline=None,
    ):  
        self.ranking_adapter = (
            ranking_adapter
            or RankingAdapter()
        )
        
        self.config = (
            config
            or RankingConfig()
        )
        
        self.ranking_sorter = (
            ranking_sorter
            or RankingSorter()
        )
        
        self.ranking_pipeline = (
            ranking_pipeline
            or RankingPipeline()
        )
    
    def _build_score_map(
        self,
        faiss_results: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        return self.ranking_adapter.build_score_map(
            faiss_results
        )
        
    def rank_candidates(
        self, 
        job: JobModel, 
        candidates: List[CandidateModel], 
        faiss_results: List[Dict[str, Any]]
    ) -> MatchResponse:
        logger.info(f"Ranking {len(candidates)} candidates for job '{job.title}' (ID: {job.id})")
        
        score_map = self._build_score_map(
            faiss_results
        )

        ranking_result = self.ranking_pipeline.process(
            job=job,
            candidates=candidates,
            score_map=score_map,
        )

        ranked_list = ranking_result.results

        metadata = ranking_result.metadata

        ranked_list = self.ranking_sorter.sort(
            ranked_list
        )
        
        logger.success(f"Successfully ranked {len(ranked_list)} qualified candidates.")
        
        return MatchResponse(
            job_id=str(job.id),
            results=ranked_list,
            metadata=metadata,
        )