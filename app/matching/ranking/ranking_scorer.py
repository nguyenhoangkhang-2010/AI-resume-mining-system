from app.matching.ranking.ranking_config import RankingConfig


class RankingScorer:

    def __init__(self, config=None):
        self.config = config or RankingConfig()

    def calculate(
        self,
        similarity_score: float,
    ) -> float:

        return (
            similarity_score
            * self.config.semantic_weight
        )