from app.matching.recommendation.bootstrap import (
    create_default_pipeline,
)
from app.matching.recommendation.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)
from app.matching.recommendation.missing_skill_analyzer import (
    MissingSkillAnalyzer,
)


class RecommendationEngine:

    def __init__(
        self,
        pipeline: RecommendationPipeline | None = None,
    ):
        self.pipeline = pipeline or create_default_pipeline()
        self.analyzer = MissingSkillAnalyzer()

    def recommend(
        self,
        required_skills: list[str],
        candidate_skills: list[str],
    ):
        return self.pipeline.process(
            required_skills=required_skills,
            candidate_skills=candidate_skills,
        )
        
    @staticmethod
    def analyze_skill_gaps(
        required_skills: list[str],
        candidate_skills: list[str],
    ) -> list[str]:

        analyzer = MissingSkillAnalyzer()

        return analyzer.analyze(
            required_skills,
            candidate_skills,
        )