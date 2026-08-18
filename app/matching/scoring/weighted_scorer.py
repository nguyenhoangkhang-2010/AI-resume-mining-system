from app.models.matching_weights import MatchingWeights


class WeightedScorer:
    """
    Combines multiple matching scores
    into a single weighted score.
    """

    def __init__(
        self,
        weights: MatchingWeights | None = None,
    ):
        self.weights = (
            weights
            or MatchingWeights()
        )

    def calculate(
        self,
        skill_score: float,
        semantic_score: float,
    ) -> float:

        score = (
            skill_score
            * self.weights.skill_weight
            + semantic_score
            * self.weights.semantic_weight
        )

        return round(score, 2)