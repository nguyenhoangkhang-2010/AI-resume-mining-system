from app.matching.ranking.ranking_config import RankingConfig


class RankingFilter:

    def __init__(self, config=None):
        self.config = config or RankingConfig()

    def accept(
        self,
        raw_score: float,
    ) -> bool:

        return (
            raw_score >= self.config.similarity_threshold
        )