from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class SkillOverlap:
    score: Optional[float]
    matched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)


class SkillOverlapScorer:
    """
    Scores how much of a job's required skills a candidate covers
    (0-100). Skills are compared case- and whitespace-insensitively.
    """

    def score(
        self,
        required_skills: Iterable[str],
        candidate_skills: Iterable[str],
    ) -> SkillOverlap:

        required = self._unique(required_skills)

        if not required:
            return SkillOverlap(score=None)

        candidate_keys = {
            self._key(skill)
            for skill in candidate_skills
            if isinstance(skill, str)
        }

        matched = [
            skill
            for skill in required
            if self._key(skill) in candidate_keys
        ]

        missing = [
            skill
            for skill in required
            if self._key(skill) not in candidate_keys
        ]

        return SkillOverlap(
            score=round(len(matched) / len(required) * 100, 2),
            matched=matched,
            missing=missing,
        )

    @staticmethod
    def _key(skill: str) -> str:
        return " ".join(skill.casefold().split())

    @classmethod
    def _unique(cls, skills: Iterable[str]) -> List[str]:
        seen = set()
        result = []

        for skill in skills:
            if not isinstance(skill, str) or not skill.strip():
                continue

            key = cls._key(skill)

            if key in seen:
                continue

            seen.add(key)
            result.append(skill)

        return result
