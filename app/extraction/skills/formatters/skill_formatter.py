from app.models.skill_match import SkillMatch


class SkillFormatter:

    @staticmethod
    def to_skill_names(
        matches: list[SkillMatch],
    ) -> list[str]:
        return [
            match.skill
            for match in matches
        ]