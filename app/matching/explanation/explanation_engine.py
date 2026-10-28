class ExplanationEngine:
    """
    Generates human-readable explanations
    for matching results.
    """

    @staticmethod
    def generate(
        skill_score: float | None,
        semantic_score: float | None,
        overall_score: float,
        experience_score: float | None = None,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> dict[str, str]:

        explanation = {}

        if skill_score is not None:
            explanation["skill_score"] = (
                f"Matched technical skills contribute {skill_score:.2f} points."
            )

        if semantic_score is not None:
            explanation["semantic_score"] = (
                f"Semantic similarity contributes {semantic_score:.2f} points."
            )

        if experience_score is not None:
            explanation["experience_score"] = (
                f"Experience level contributes {experience_score:.2f} points."
            )

        if matched_skills:
            explanation["matched_skills"] = (
                "Matched skills: " + ", ".join(matched_skills) + "."
            )

        if missing_skills:
            explanation["missing_skills"] = (
                "Missing skills: " + ", ".join(missing_skills) + "."
            )

        explanation["overall_score"] = (
            f"Final weighted score is {overall_score:.2f}."
        )

        return explanation
