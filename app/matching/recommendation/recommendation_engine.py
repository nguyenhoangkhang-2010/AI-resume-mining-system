from app.matching.recommendation.bootstrap import (
    create_default_pipeline,
)
from app.matching.recommendation.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)


class RecommendationEngine:

    def __init__(
        self,
        pipeline: RecommendationPipeline | None = None,
    ):
        self.pipeline = pipeline or create_default_pipeline()

    def recommend(
        self,
        required_skills: list[str],
        candidate_skills: list[str],
    ):
        return self.pipeline.process(
            required_skills=required_skills,
            candidate_skills=candidate_skills,
        )