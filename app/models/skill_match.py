from dataclasses import dataclass


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    confidence: float
    source: str