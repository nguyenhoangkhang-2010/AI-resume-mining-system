from app.matching.recommendation.providers.provider_registry import (
    RecommendationProviderRegistry,
)

from app.matching.recommendation.retrievers.recommendation_retriever import (
    RecommendationRetriever,
)

from app.schemas.recommendation_schema import RecommendationItem


class DefaultRecommendationRetriever(
    RecommendationRetriever,
):

    def __init__(
        self,
        registry: RecommendationProviderRegistry,
    ):
        self.registry = registry


    def retrieve(
        self,
        missing_skills: list[str],
    ) -> list[RecommendationItem]:

        recommendations = []

        for skill in missing_skills:
            recommendations.extend(
                self.registry.get_recommendations(
                    skill
                )
            )

        return recommendations



class StaticRecommendationRetriever(
    RecommendationRetriever,
):

    """
    Backward compatible retriever.
    
    Used by old tests and old pipeline code.
    """

    def __init__(
        self,
        provider,
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