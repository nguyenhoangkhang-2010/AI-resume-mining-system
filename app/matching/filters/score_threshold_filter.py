from app.models.matching_score import MatchingScore


class ScoreThresholdFilter:
    """
    Filters matching results using
    a configurable minimum score.
    """

    def __init__(
        self,
        threshold: float = 60.0,
    ):
        self.threshold = threshold

    def accept(
        self,
        score: MatchingScore,
    ) -> bool:

        return (
            score.overall_score
            >= self.threshold
        )