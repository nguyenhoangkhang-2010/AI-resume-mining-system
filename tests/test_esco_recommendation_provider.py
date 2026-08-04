from app.matching.recommendation.providers.esco_recommendation_provider import (
    EscoRecommendationProvider,
)


def test_esco_recommendation_provider():

    provider = EscoRecommendationProvider()

    result = provider.get_recommendations(
        "manage musical staff"
    )

    assert len(result) == 1

    assert result[0].type == "skill"

    assert result[0].source == "ESCO"