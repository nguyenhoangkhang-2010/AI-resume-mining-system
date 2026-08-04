from app.matching.recommendation.missing_skill_analyzer import (
    MissingSkillAnalyzer,
)

from app.matching.recommendation.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)

from app.matching.recommendation.recommendation_builder import (
    RecommendationBuilder,
)

from app.matching.recommendation.retrievers.static_recommendation_retriever import (
    StaticRecommendationRetriever,
)


def test_recommendation_pipeline():

    pipeline = RecommendationPipeline(
        analyzer=MissingSkillAnalyzer(),
        retriever=StaticRecommendationRetriever(),
        builder=RecommendationBuilder(),
    )

    result = pipeline.process(
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