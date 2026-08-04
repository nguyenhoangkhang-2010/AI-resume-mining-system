from app.matching.recommendation.retrievers.static_recommendation_retriever import (
    StaticRecommendationRetriever,
)

from tests.fakes.fake_recommendation_provider import (
    FakeRecommendationProvider,
)


def test_static_recommendation_retriever():

    retriever = StaticRecommendationRetriever(
        provider=FakeRecommendationProvider(),
    )

    result = retriever.retrieve(
        [
            "Python",
            "Docker",
        ]
    )

    assert len(result) == 2

    assert result[0].title == "Learn Python"

    assert result[1].title == "Learn Docker"