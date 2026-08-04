from app.matching.recommendation.retrievers.recommendation_retriever import (
    RecommendationRetriever,
)

from app.schemas.recommendation_schema import (
    RecommendationItem,
)


class StaticRecommendationRetriever(
    RecommendationRetriever,
):

    def retrieve(
        self,
        missing_skills: list[str],
    ) -> list[RecommendationItem]:

        return [
            RecommendationItem(
                type="course",
                title=f"Learn {skill}",
                priority="medium",
            )
            for skill in missing_skills
        ]