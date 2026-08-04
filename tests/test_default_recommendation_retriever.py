from app.matching.recommendation.retrievers.recommendation_retriever_impl import (
    DefaultRecommendationRetriever,
)

from app.matching.recommendation.providers.provider_registry import (
    RecommendationProviderRegistry,
)

from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import RecommendationItem



class FakeProvider(
    RecommendationProvider,
):

    def get_recommendations(
        self,
        skill: str,
    ):

        return [
            RecommendationItem(
                type="skill",
                title=skill,
                priority="medium",
            )
        ]



def test_default_recommendation_retriever():

    registry = RecommendationProviderRegistry(
        providers=[
            FakeProvider()
        ]
    )


    retriever = DefaultRecommendationRetriever(
        registry
    )


    result = retriever.retrieve(
        [
            "Docker",
            "Python",
        ]
    )


    assert len(result) == 2