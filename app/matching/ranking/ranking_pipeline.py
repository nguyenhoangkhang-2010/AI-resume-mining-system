from typing import List, Dict

from app.models.job import JobModel
from app.models.candidate import CandidateModel

from app.matching.ranking.ranking_filter import RankingFilter
from app.matching.ranking.ranking_builder import RankingBuilder
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.recommendation.recommendation_engine import RecommendationEngine
from app.schemas.ranking_result import RankingResult
from app.matching.ranking.ranking_scorer import RankingScorer
from app.matching.ranking.ranking_sorter import RankingSorter


class RankingPipeline:

    def __init__(
        self,
        similarity_engine=None,
        recommendation_engine=None,
        ranking_filter=None,
        ranking_scorer=None,
        ranking_builder=None,
        ranking_sorter=None,
    ):
        self.similarity_engine = (
            similarity_engine
            or SimilarityEngine()
        )

        self.recommendation_engine = (
            recommendation_engine
            or RecommendationEngine()
        )

        self.ranking_filter = (
            ranking_filter
            or RankingFilter()
        )

        self.ranking_builder = (
            ranking_builder
            or RankingBuilder()
        )
        
        self.ranking_scorer = (
            ranking_scorer
            or RankingScorer()
        )
        
        self.ranking_sorter = (
            ranking_sorter
            or RankingSorter()
        )

    def process(
        self,
        job: JobModel,
        candidates: List[CandidateModel],
        score_map: Dict[str, float],
    ) -> RankingResult:

        ranked_list = []
        filtered_candidates = 0

        for candidate in candidates:

            if candidate.faiss_id not in score_map:
                continue

            raw_score = score_map[candidate.faiss_id]

            if not self.ranking_filter.accept(raw_score):
                filtered_candidates += 1
                continue

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

            ranking_score = self.ranking_scorer.calculate(
                similarity_score=normalized_score,
                skill_gaps=skill_gaps,
            )

            ranked_candidate = self.ranking_builder.build(
                candidate=candidate,
                similarity_score=ranking_score,
                skill_gaps=skill_gaps,
            )

            ranked_list.append(
                ranked_candidate
            )
            
        ranked_list = self.ranking_sorter.sort(
            ranked_list
        )

        return RankingResult(
            results=ranked_list,
            metadata={
                "total_candidates": len(candidates),
                "ranked_candidates": len(ranked_list),
                "filtered_candidates": filtered_candidates,
                "similarity_threshold": (
                    self.ranking_filter.config.similarity_threshold
                ),
            }
        )