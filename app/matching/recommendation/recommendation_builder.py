from app.schemas.recommendation_schema import (
    RecommendationItem,
    RecommendationResponse,
)


class RecommendationBuilder:
    @staticmethod
    def build(
        recommendations: list[RecommendationItem],
    ) -> RecommendationResponse:

        return RecommendationResponse(
            recommendations=recommendations,
        )