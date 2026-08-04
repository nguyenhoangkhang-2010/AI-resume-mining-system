from app.schemas.recommendation_schema import (
    RecommendationItem,
    RecommendationResponse,
)


def test_recommendation_schema():

    item = RecommendationItem(
        type="missing_skill",
        title="Docker",
        priority="high",
    )

    result = RecommendationResponse(
        recommendations=[item]
    )

    assert result.recommendations[0].title == "Docker"