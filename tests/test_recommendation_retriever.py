from app.matching.recommendation.retrievers.static_recommendation_retriever import (
    StaticRecommendationRetriever,
)

def test_static_recommendation_retriever():
    retriever = StaticRecommendationRetriever()

    result = retriever.retrieve(
        [
            "Python",
            "Docker",
        ]
    )

    assert len(result) == 2

    assert result[0].title == "Learn Python"

    assert result[1].title == "Learn Docker"