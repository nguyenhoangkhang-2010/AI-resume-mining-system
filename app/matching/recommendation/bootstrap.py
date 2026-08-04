from app.matching.recommendation.missing_skill_analyzer import (
    MissingSkillAnalyzer,
)

from app.matching.recommendation.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)

from app.matching.recommendation.recommendation_builder import (
    RecommendationBuilder,
)

from app.matching.recommendation.providers.provider_registry import (
    RecommendationProviderRegistry,
)

from app.matching.recommendation.providers.esco_recommendation_provider import (
    EscoRecommendationProvider,
)

from app.matching.recommendation.providers.static_recommendation_provider import (
    StaticRecommendationProvider,
)

from app.matching.recommendation.retrievers.recommendation_retriever_impl import (
    DefaultRecommendationRetriever,
)
from app.matching.recommendation.providers.industry_skill_provider import (
    IndustrySkillProvider,
)


def create_default_pipeline():

    registry = RecommendationProviderRegistry(
        providers=[
            EscoRecommendationProvider(),
            IndustrySkillProvider(),
            StaticRecommendationProvider(),
        ]
    )

    return RecommendationPipeline(
        analyzer=MissingSkillAnalyzer(),

        retriever=DefaultRecommendationRetriever(
            registry
        ),

        builder=RecommendationBuilder(),
    )