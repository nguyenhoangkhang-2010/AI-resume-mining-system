from typing import List, Dict, Any
from loguru import logger

from app.matching.ranking.ranking_config import (
    RankingConfig,
)
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.candidate_schema import CandidateResponse
from app.schemas.matching_schema import RankedCandidate, MatchResponse
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.recommendation.recommendation_engine import RecommendationEngine
from app.matching.ranking.ranking_adapter import RankingAdapter
from app.matching.ranking.ranking_sorter import RankingSorter
from app.matching.ranking.ranking_filter import (
    RankingFilter,
)
from app.matching.ranking.ranking_builder import (
    RankingBuilder,
)


class RankingEngine:
    
    def __init__(
        self,
        similarity_engine=None,
        recommendation_engine=None,
        ranking_adapter=None,
        config=None,
        ranking_sorter=None,
        ranking_filter=None,
        ranking_builder=None,
    ):
        self.similarity_engine = (
            similarity_engine
            or SimilarityEngine()
        )

        self.recommendation_engine = (
            recommendation_engine
            or RecommendationEngine()
        )
        
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
        
        self.ranking_filter = (
            ranking_filter
            or RankingFilter(self.config)
        )
        
        self.ranking_builder = (
            ranking_builder
            or RankingBuilder()
        )
    
    def _build_score_map(
        self,
        faiss_results,
    ):
        return self.ranking_adapter.build_score_map(
            faiss_results
        )
        
    def _is_candidate_valid(
        self,
        candidate,
        score_map,
    ):
        return (
            candidate.faiss_id in score_map
        )
        
    def _build_ranked_candidate(
        self,
        job,
        candidate,
        raw_score,
    ):
        normalized_score = (
            self.similarity_engine.normalize_score(
                raw_score
            )
        )

        skill_gaps = (
            self.recommendation_engine.analyze_skill_gaps(
                required_skills=job.required_skills,
                candidate_skills=candidate.skills,
            )
        )

        return self.ranking_builder.build(
            candidate=candidate,
            similarity_score=normalized_score,
            skill_gaps=skill_gaps,
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
        
        ranked_list: List[RankedCandidate] = []
        
        for candidate in candidates:
            if not self._is_candidate_valid(
                candidate,
                score_map,
            ):
                continue
                
            raw_score = score_map[candidate.faiss_id]
            
            if not self.ranking_filter.accept(raw_score):
                logger.debug(
                    f"Candidate {candidate.id} rejected."
                )
                continue
                
            ranked_candidate = (
                self._build_ranked_candidate(
                    job,
                    candidate,
                    raw_score,
                )
            )

            ranked_list.append(
                ranked_candidate
            )
        
        ranked_list = self.ranking_sorter.sort(
            ranked_list
        )
        
        logger.success(f"Successfully ranked {len(ranked_list)} qualified candidates.")
        
        return MatchResponse(job_id=str(job.id), results=ranked_list)