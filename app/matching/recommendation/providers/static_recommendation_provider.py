from app.schemas.recommendation_schema import RecommendationItem
from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)


class StaticRecommendationProvider(
    RecommendationProvider,
):

    DATA = {
        "python": [
            RecommendationItem(
                type="course",
                title="Learn Python",
                priority="high",
            )
        ],
        "docker": [
            RecommendationItem(
                type="course",
                title="Learn Docker",
                priority="medium",
            )
        ],
    }

    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        return self.DATA.get(
            skill.lower(),
            [],
        )