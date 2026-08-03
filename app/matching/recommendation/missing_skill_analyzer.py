from loguru import logger


class MissingSkillAnalyzer:
    def analyze(
        self,
        required_skills: list[str],
        candidate_skills: list[str],
    ) -> list[str]:

        if not required_skills:
            return []

        candidate_skill_set = {
            skill.strip().lower()
            for skill in candidate_skills
        }

        missing_skills = [
            skill.strip()
            for skill in required_skills
            if skill.strip().lower() not in candidate_skill_set
        ]

        logger.debug(
            f"Analyzed skill gaps: found {len(missing_skills)} missing out of {len(required_skills)} required."
        )

        return missing_skills