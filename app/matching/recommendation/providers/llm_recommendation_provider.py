from abc import ABC, abstractmethod

from app.schemas.recommendation_schema import RecommendationItem


class LLMRecommendationProvider(ABC):

    @abstractmethod
    def generate_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:
        ...