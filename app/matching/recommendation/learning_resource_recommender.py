from app.schemas.recommendation_schema import RecommendationItem


class LearningResourceRecommender:
    def recommend(
        self,
        missing_skills: list[str],
    ) -> list[RecommendationItem]:

        recommendations = []

        for skill in missing_skills:
            recommendations.append(
                RecommendationItem(
                    type="learning_resource",
                    title=f"Learn {skill}",
                    priority="high",
                )
            )

        return recommendations