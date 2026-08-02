from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    """
    Defines weights for different matching components.
    """

    skill_weight: float = 0.6
    semantic_weight: float = 0.4


class WeightedScorer:
    """
    Combines multiple matching scores
    into a single weighted score.
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
    ):
        self.weights = (
            weights
            or ScoringWeights()
        )

    def calculate(
        self,
        skill_score: float,
        semantic_score: float,
    ) -> float:

        score = (
            skill_score
            * self.weights.skill_weight
            +
            semantic_score
            * self.weights.semantic_weight
        )

        return round(
            score,
            2
        )