from app.schemas.recommendation_schema import RecommendationResponse


class RecommendationBuilder:
    @staticmethod
    def build(
        missing_skills: list[str],
    ) -> RecommendationResponse:
        return RecommendationResponse(
            missing_skills=missing_skills,
        )