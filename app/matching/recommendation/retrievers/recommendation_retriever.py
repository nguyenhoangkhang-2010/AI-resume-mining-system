from abc import ABC
from abc import abstractmethod

from app.schemas.recommendation_schema import (
    RecommendationItem,
)


class RecommendationRetriever(ABC):

    @abstractmethod
    def retrieve(
        self,
        missing_skills: list[str],
    ) -> list[RecommendationItem]:
        ...