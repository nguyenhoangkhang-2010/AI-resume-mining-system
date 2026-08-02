from app.models.skill_match import SkillMatch


class ConfidenceFilter:

    def __init__(
        self,
        minimum_confidence: float = 0.70,
    ):
        self.minimum_confidence = minimum_confidence

    def filter(
        self,
        matches: list[SkillMatch],
    ) -> list[SkillMatch]:

        return [
            match
            for match in matches
            if match.confidence >= self.minimum_confidence
        ]