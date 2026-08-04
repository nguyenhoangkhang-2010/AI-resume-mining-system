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
    ) -> list[RecommendationItem]:

        return [
            RecommendationItem(
                type="skill",
                title=f"{skill} recommendation",
                priority="medium",
            )
        ]


def test_provider_registry():

    registry = RecommendationProviderRegistry(
        providers=[
            FakeProvider(),
            FakeProvider(),
        ]
    )

    result = registry.get_recommendations(
        "Docker"
    )


    assert len(result) == 2