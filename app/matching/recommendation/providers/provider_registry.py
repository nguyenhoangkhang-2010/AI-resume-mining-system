from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import (
    RecommendationItem,
)


class RecommendationProviderRegistry:

    def __init__(
        self,
        providers: list[RecommendationProvider],
    ):
        self.providers = providers


    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        recommendations = []

        for provider in self.providers:

            recommendations.extend(
                provider.get_recommendations(
                    skill
                )
            )

        return recommendations