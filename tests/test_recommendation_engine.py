from app.matching.recommendation.recommendation_engine import (
    RecommendationEngine,
)


def test_recommendation_engine():

    engine = RecommendationEngine()

    result = engine.recommend(
        required_skills=[
            "Python",
            "Docker",
        ],
        candidate_skills=[
            "Python",
        ],
    )

    assert len(result.recommendations) == 1

    assert result.recommendations[0].title == "Learn Docker"