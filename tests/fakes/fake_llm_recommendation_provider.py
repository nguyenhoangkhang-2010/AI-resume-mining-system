from app.matching.recommendation.providers.llm_recommendation_provider import (
    LLMRecommendationProvider,
)

from app.schemas.recommendation_schema import RecommendationItem


class FakeLLMRecommendationProvider(
    LLMRecommendationProvider,
):

    def generate_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        return [
            RecommendationItem(
                type="course",
                title=f"AI recommendation for {skill}",
                priority="high",
            )
        ]