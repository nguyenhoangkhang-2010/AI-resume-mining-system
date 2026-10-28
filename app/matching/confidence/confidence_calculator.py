class ConfidenceCalculator:
    """
    Estimates confidence for
    a matching result.
    """

    @staticmethod
    def calculate(
        skill_score: float | None,
        semantic_score: float | None,
        experience_score: float | None = None,
    ) -> float:

        scores = [
            score
            for score in (
                skill_score,
                semantic_score,
                experience_score,
            )
            if score is not None
        ]

        if not scores:
            return 0.0

        return round(
            sum(scores) / len(scores),
            2,
        )
