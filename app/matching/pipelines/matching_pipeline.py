from app.models.matching_score import MatchingScore

from app.matching.scoring.weighted_scorer import (
    WeightedScorer,
)


class MatchingPipeline:
    """
    Combines matching components into
    a single matching result.
    """

    def __init__(self):

        self.scorer = WeightedScorer()

    def process(
        self,
        candidate_id: str,
        job_id: str,
        skill_score: float,
        semantic_score: float,
    ) -> MatchingScore:

        overall_score = self.scorer.calculate(
            skill_score=skill_score,
            semantic_score=semantic_score,
        )

        return MatchingScore(
            candidate_id=candidate_id,
            job_id=job_id,
            skill_score=skill_score,
            semantic_score=semantic_score,
            overall_score=overall_score,
        )