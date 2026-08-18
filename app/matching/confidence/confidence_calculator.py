class ConfidenceCalculator:
    """
    Estimates confidence for
    a matching result.
    """

    @staticmethod
    def calculate(
        skill_score: float,
        semantic_score: float,
    ) -> float:

        confidence = (
            skill_score + semantic_score
        ) / 2

        return round(confidence, 2)