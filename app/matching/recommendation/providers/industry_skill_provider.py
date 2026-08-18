from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import (
    RecommendationItem,
)


class IndustrySkillProvider(
    RecommendationProvider,
):

    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        return []