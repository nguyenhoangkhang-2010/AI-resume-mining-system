from tests.fakes.fake_llm_recommendation_provider import (
    FakeLLMRecommendationProvider,
)


def test_llm_provider():

    provider = FakeLLMRecommendationProvider()

    result = provider.generate_recommendations(
        "Python"
    )

    assert result[0].priority == "high"