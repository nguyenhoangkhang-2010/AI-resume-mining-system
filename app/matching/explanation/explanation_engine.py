class ExplanationEngine:
    """
    Generates human-readable explanations
    for matching results.
    """

    @staticmethod
    def generate(
        skill_score: float,
        semantic_score: float,
        overall_score: float,
    ) -> dict[str, str]:

        return {
            "skill_score":
                f"Matched technical skills contribute {skill_score:.2f} points.",

            "semantic_score":
                f"Semantic similarity contributes {semantic_score:.2f} points.",

            "overall_score":
                f"Final weighted score is {overall_score:.2f}.",
        }