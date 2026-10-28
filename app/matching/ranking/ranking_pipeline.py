from typing import List, Dict

from app.models.job import JobModel
from app.models.candidate import CandidateModel

from app.matching.filters.score_threshold_filter import ScoreThresholdFilter
from app.matching.ranking.ranking_filter import RankingFilter
from app.matching.ranking.ranking_builder import RankingBuilder
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.recommendation.recommendation_engine import RecommendationEngine
from app.schemas.ranked_candidate_schema import ScoreBreakdown
from app.schemas.ranking_result import RankingResult
from app.matching.ranking.ranking_scorer import RankingScorer
from app.matching.ranking.ranking_sorter import RankingSorter


class RankingPipeline:
    """
    Ranks retrieved candidates for a job.

    With a candidate_scorer the pipeline runs in hybrid mode: each
    candidate gets a skill / semantic / experience score and is kept
    only if the final score reaches the configured minimum. Without
    one it falls back to ranking by cosine similarity alone.
    """

    def __init__(
        self,
        similarity_engine=None,
        recommendation_engine=None,
        ranking_filter=None,
        ranking_scorer=None,
        ranking_builder=None,
        ranking_sorter=None,
        candidate_scorer=None,
        score_filter=None,
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

        self.candidate_scorer = candidate_scorer

        self.score_filter = score_filter or ScoreThresholdFilter(
            threshold=self.ranking_filter.config.min_overall_score,
        )

    def process(
        self,
        job: JobModel,
        candidates: List[CandidateModel],
        score_map: Dict[str, float],
    ) -> RankingResult:

        ranked_list = []
        filtered_candidates = 0
        hybrid = self.candidate_scorer is not None

        for candidate in candidates:

            if candidate.faiss_id not in score_map:
                continue

            raw_score = score_map[candidate.faiss_id]

            if hybrid:
                ranked_candidate = self._rank_hybrid(
                    job,
                    candidate,
                    raw_score,
                )
            else:
                ranked_candidate = self._rank_by_similarity(
                    job,
                    candidate,
                    raw_score,
                )

            if ranked_candidate is None:
                filtered_candidates += 1
                continue

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
                    self.score_filter.threshold
                    if hybrid
                    else self.ranking_filter.config.similarity_threshold
                ),
                "scoring_mode": "hybrid" if hybrid else "similarity",
            }
        )

    def _rank_hybrid(
        self,
        job,
        candidate,
        raw_score: float,
    ):

        semantic_score = (
            self.similarity_engine.normalize_score(
                raw_score
            )
        )

        matching_score = self.candidate_scorer.score(
            job=job,
            candidate=candidate,
            semantic_score=semantic_score,
        )

        if not self.score_filter.accept(matching_score):
            return None

        return self.ranking_builder.build(
            candidate=candidate,
            similarity_score=matching_score.overall_score,
            skill_gaps=matching_score.missing_skills,
            score_breakdown=ScoreBreakdown(
                skill_score=matching_score.skill_score,
                semantic_score=matching_score.semantic_score,
                experience_score=matching_score.experience_score,
                confidence_score=matching_score.confidence_score,
                matched_skills=matching_score.matched_skills,
                explanation=matching_score.explanation or {},
            ),
        )

    def _rank_by_similarity(
        self,
        job,
        candidate,
        raw_score: float,
    ):

        if not self.ranking_filter.accept(raw_score):
            return None

        normalized_score = (
            self.similarity_engine.normalize_score(
                raw_score
            )
        )

        skill_gaps = [
            skill
            for skill in job.required_skills
            if skill not in candidate.skills
        ]

        ranking_score = self.ranking_scorer.calculate(
            similarity_score=normalized_score,
            skill_gaps=skill_gaps,
        )

        return self.ranking_builder.build(
            candidate=candidate,
            similarity_score=ranking_score,
            skill_gaps=skill_gaps,
        )
