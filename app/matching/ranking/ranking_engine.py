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


class RankingEngine:
    
    def __init__(
        self,
        similarity_engine=None,
        recommendation_engine=None,
        ranking_adapter=None,
        config=None,
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

    def sort_candidates(
        self,
        candidates: List[RankedCandidate],
    ) -> List[RankedCandidate]:
        """
        Sort candidates by similarity score descending.
        """

        return sorted(
            candidates,
            key=lambda x: x.similarity_score,
            reverse=True,
        )

    def rank_candidates(
        self, 
        job: JobModel, 
        candidates: List[CandidateModel], 
        faiss_results: List[Dict[str, Any]]
    ) -> MatchResponse:
        logger.info(f"Ranking {len(candidates)} candidates for job '{job.title}' (ID: {job.id})")
        
        score_map = self.ranking_adapter.build_score_map(
            faiss_results
        )
        
        ranked_list: List[RankedCandidate] = []
        
        for candidate in candidates:
            if candidate.faiss_id not in score_map:
                continue
                
            raw_score = score_map[candidate.faiss_id]
            
            if raw_score < self.config.similarity_threshold:
                logger.debug(f"Candidate {candidate.id} rejected. Score {raw_score:.3f} < threshold {self.config.similarity_threshold}")
                continue
                
            normalized_score = self.similarity_engine.normalize_score(raw_score)
            
            skill_gaps = self.recommendation_engine.analyze_skill_gaps(
                required_skills=job.required_skills,
                candidate_skills=candidate.skills
            )
            
            ranked_candidate = RankedCandidate(
                similarity_score=normalized_score,
                skill_gaps=skill_gaps,
                candidate_profile=CandidateResponse.model_validate(candidate)
            )
            ranked_list.append(ranked_candidate)
        
        ranked_list = self.sort_candidates(
            ranked_list
        )
        logger.success(f"Successfully ranked {len(ranked_list)} qualified candidates.")
        
        return MatchResponse(job_id=str(job.id), results=ranked_list)