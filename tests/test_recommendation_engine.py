from app.matching.recommendation.recommendation_engine import (
    RecommendationEngine,
)


def test_recommend_missing_skills():

    engine = RecommendationEngine()

    result = engine.recommend(
        required_skills=[
            "Python",
            "SQL",
            "Docker",
        ],
        candidate_skills=[
            "Python",
        ],
    )

    assert result.missing_skills == [
        "SQL",
        "Docker",
    ]