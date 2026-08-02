from app.extraction.job.requirement_extractor import RequirementExtractor
from app.extraction.job.responsibility_extractor import ResponsibilityExtractor
from app.extraction.job.job_skill_extractor import JobSkillExtractor


class JobExtractor:

    def __init__(self):
        self.skill_extractor = JobSkillExtractor()

    def extract(
        self,
        text: str,
    ) -> dict:

        return {
            "requirements": RequirementExtractor.extract(text),
            "responsibilities": ResponsibilityExtractor.extract(text),
            "skills": self.skill_extractor.extract(text),
        }