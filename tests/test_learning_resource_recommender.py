from app.matching.recommendation.learning_resource_recommender import (
    LearningResourceRecommender,
)


def test_learning_resource_recommender():

    recommender = LearningResourceRecommender()

    result = recommender.recommend(
        [
            "Docker",
            "Kubernetes",
        ]
    )

    assert len(result) == 2

    assert result[0].type == "learning_resource"

    assert result[0].title == "Learn Docker"

    assert result[1].title == "Learn Kubernetes"