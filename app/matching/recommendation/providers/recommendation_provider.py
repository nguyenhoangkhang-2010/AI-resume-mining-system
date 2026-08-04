from abc import ABC, abstractmethod

from app.schemas.recommendation_schema import RecommendationItem


class RecommendationProvider(ABC):

    @abstractmethod
    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:
        ...