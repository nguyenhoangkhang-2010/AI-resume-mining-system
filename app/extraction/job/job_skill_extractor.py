from app.extraction.skills.skill_extractor import SkillExtractor


class JobSkillExtractor:

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def extract(
        self,
        text: str,
    ) -> list[str]:

        return self.skill_extractor.extract(text)