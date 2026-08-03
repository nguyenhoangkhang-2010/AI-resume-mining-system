from app.matching.recommendation.missing_skill_analyzer import MissingSkillAnalyzer
from app.matching.recommendation.recommendation_builder import RecommendationBuilder


class RecommendationEngine:
    def __init__(
        self,
        analyzer: MissingSkillAnalyzer | None = None,
        builder: RecommendationBuilder | None = None,
    ):
        self.analyzer = analyzer or MissingSkillAnalyzer()
        self.builder = builder or RecommendationBuilder()

    def recommend(
        self,
        required_skills: list[str],
        candidate_skills: list[str],
    ):
        missing = self.analyzer.analyze(
            required_skills,
            candidate_skills,
        )

        return self.builder.build(
            missing_skills=missing,
        )