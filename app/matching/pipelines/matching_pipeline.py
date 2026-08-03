from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)


class MatchingPipeline:

    def __init__(self):
        self.strategy = HybridMatchingStrategy()

    def process(
        self,
        candidate_id,
        job_id,
        skill_score,
        semantic_score,
    ):
        return self.strategy.match(
            candidate_id,
            job_id,
            skill_score,
            semantic_score,
        )