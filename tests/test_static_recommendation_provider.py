from app.matching.recommendation.providers.static_recommendation_provider import (
    StaticRecommendationProvider,
)


def test_static_recommendation_provider():

    provider = StaticRecommendationProvider()

    result = provider.get_recommendations("Python")

    assert len(result) == 1
    assert result[0].title == "Learn Python"