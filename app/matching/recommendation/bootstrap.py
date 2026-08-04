from app.matching.recommendation.missing_skill_analyzer import MissingSkillAnalyzer
from app.matching.recommendation.pipelines.recommendation_pipeline import RecommendationPipeline
from app.matching.recommendation.recommendation_builder import RecommendationBuilder
from app.matching.recommendation.retrievers.static_recommendation_retriever import (
    StaticRecommendationRetriever,
)


def create_default_pipeline():

    return RecommendationPipeline(
        analyzer=MissingSkillAnalyzer(),
        retriever=StaticRecommendationRetriever(),
        builder=RecommendationBuilder(),
    )