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

        requirements = RequirementExtractor.extract(text)

        # Skills are read from the requirements section when there is one.
        # Running the semantic matcher over the whole description also turns
        # the title and responsibilities prose into spurious skills (for
        # example "data science" from a data engineer posting), which then
        # count against every candidate.
        skill_source = requirements or text

        return {
            "requirements": requirements,
            "responsibilities": ResponsibilityExtractor.extract(text),
            "skills": self.skill_extractor.extract(skill_source),
        }
