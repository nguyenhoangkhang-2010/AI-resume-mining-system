from app.matching.ranking.ranking_config import RankingConfig


class RankingScorer:

    def __init__(self, config=None):
        self.config = config or RankingConfig()

    def calculate(
        self,
        similarity_score: float,
        skill_gaps: list[str],
    ) -> float:

        final_score = (
            similarity_score
            * self.config.semantic_weight
        )

        penalty = (
            len(skill_gaps)
            * self.config.penalty_per_missing_skill
        )

        final_score -= penalty

        return max(0.0, final_score)