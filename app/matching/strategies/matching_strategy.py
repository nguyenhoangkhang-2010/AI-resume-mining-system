from abc import ABC, abstractmethod

from app.models.matching_score import MatchingScore


class MatchingStrategy(ABC):
    @abstractmethod
    def match(
        self,
        candidate_id: str,
        job_id: str,
        skill_score: float,
        semantic_score: float,
    ) -> MatchingScore:
        ...