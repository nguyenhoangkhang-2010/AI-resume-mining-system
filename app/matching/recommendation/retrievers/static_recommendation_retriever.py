from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.matching.recommendation.retrievers.recommendation_retriever import (
    RecommendationRetriever,
)

from app.schemas.recommendation_schema import RecommendationItem


class StaticRecommendationRetriever(
    RecommendationRetriever,
):

    def __init__(
        self,
        provider: RecommendationProvider,
    ):
        self.provider = provider

    def retrieve(
        self,
        missing_skills: list[str],
    ) -> list[RecommendationItem]:

        recommendations = []

        for skill in missing_skills:
            recommendations.extend(
                self.provider.get_recommendations(skill)
            )

        return recommendations