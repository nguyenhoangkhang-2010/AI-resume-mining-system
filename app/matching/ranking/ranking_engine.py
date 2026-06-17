from typing import List, Dict, Any
from loguru import logger

from app.core.constants.app_constants import SIMILARITY_THRESHOLD
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.candidate_schema import CandidateResponse
from app.schemas.matching_schema import RankedCandidate, MatchResponse
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.recommendation.recommendation_engine import RecommendationEngine


class RankingEngine:
    
    def __init__(self):
        self.similarity_engine = SimilarityEngine()
        self.recommendation_engine = RecommendationEngine()

    def rank_candidates(
        self, 
        job: JobModel, 
        candidates: List[CandidateModel], 
        faiss_results: List[Dict[str, Any]]
    ) -> MatchResponse:
        logger.info(f"Ranking {len(candidates)} candidates for job '{job.title}' (ID: {job.id})")
        
        score_map = {result["faiss_id"]: result["similarity_score"] for result in faiss_results}
        
        ranked_list: List[RankedCandidate] = []
        
        for candidate in candidates:
            if candidate.faiss_id not in score_map:
                continue
                
            raw_score = score_map[candidate.faiss_id]
            
            if raw_score < SIMILARITY_THRESHOLD:
                logger.debug(f"Candidate {candidate.id} rejected. Score {raw_score:.3f} < threshold {SIMILARITY_THRESHOLD}")
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
        
        ranked_list.sort(key=lambda x: x.similarity_score, reverse=True)
        logger.success(f"Successfully ranked {len(ranked_list)} qualified candidates.")
        
        return MatchResponse(job_id=str(job.id), results=ranked_list)