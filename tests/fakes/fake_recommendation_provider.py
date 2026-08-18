from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import RecommendationItem


class FakeRecommendationProvider(
    RecommendationProvider,
):
    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        return [
            RecommendationItem(
                type="course",
                title=f"Learn {skill}",
                priority="medium",
            )
        ]