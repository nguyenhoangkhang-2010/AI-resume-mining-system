from app.models.matching_score import MatchingScore
from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)
from app.matching.filters.score_threshold_filter import (
    ScoreThresholdFilter,
)


class MatchingPipeline:

    def __init__(self):
        self.strategy = HybridMatchingStrategy()
        self.filter = ScoreThresholdFilter()

    def process(
        self,
        candidate_id,
        job_id,
        skill_score,
        semantic_score,
    ) -> MatchingScore | None:
        result = self.strategy.match(
            candidate_id=candidate_id,
            job_id=job_id,
            skill_score=skill_score,
            semantic_score=semantic_score,
        )
        
        if not self.filter.accept(result):
            return None

        return result