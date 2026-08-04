from app.matching.recommendation.missing_skill_analyzer import (
    MissingSkillAnalyzer,
)

from app.matching.recommendation.recommendation_builder import (
    RecommendationBuilder,
)

from app.matching.recommendation.retrievers.recommendation_retriever import (
    RecommendationRetriever,
)

from app.schemas.recommendation_schema import RecommendationResponse


class RecommendationPipeline:

    def __init__(
        self,
        analyzer: MissingSkillAnalyzer,
        retriever: RecommendationRetriever,
        builder: RecommendationBuilder,
    ):
        self.analyzer = analyzer
        self.retriever = retriever
        self.builder = builder

    def process(
        self,
        required_skills: list[str],
        candidate_skills: list[str],
    ) -> RecommendationResponse:

        missing_skills = self.analyzer.analyze(
            required_skills,
            candidate_skills,
        )

        recommendations = self.retriever.retrieve(
            missing_skills,
        )

        return self.builder.build(
            recommendations,
        )