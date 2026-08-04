from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import RecommendationItem


class EscoRecommendationProvider(
    RecommendationProvider,
):

    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        return [
            RecommendationItem(
                type="skill",
                title=f"Related ESCO skill for {skill}",
                priority="medium",
            )
        ]