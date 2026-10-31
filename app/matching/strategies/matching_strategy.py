from abc import ABC, abstractmethod

from app.models.matching_score import MatchingScore


class MatchingStrategy(ABC):
    @abstractmethod
    def match(
        self,
        candidate_id: str,
        job_id: str,
        skill_score: float | None,
        semantic_score: float | None,
        experience_score: float | None = None,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> MatchingScore:
        ...
