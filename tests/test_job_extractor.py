from app.extraction.job.job_extractor import JobExtractor


def test_job_extractor():

    text = """
Software Engineer

Requirements

Python
FastAPI
Docker

Responsibilities

Develop APIs
Write tests
"""

    extractor = JobExtractor()

    result = extractor.extract(text)

    assert "Python" in result["requirements"]
    assert "Develop APIs" in result["responsibilities"]
    assert isinstance(result["skills"], list)

class RecordingSkillExtractor:
    def __init__(self):
        self.received = None

    def extract(self, text):
        self.received = text
        return ["python"]


def make_extractor():
    extractor = JobExtractor.__new__(JobExtractor)
    extractor.skill_extractor = RecordingSkillExtractor()

    return extractor


def test_skills_are_extracted_from_the_requirements_section_only():
    extractor = make_extractor()

    result = extractor.extract(
        "Data Engineer\n\nRequirements\n\nPython\nSQL\n\n"
        "Responsibilities\n\nBuild data pipelines\n"
    )

    assert extractor.skill_extractor.received == "Python\nSQL"
    assert result["skills"] == ["python"]


def test_skills_fall_back_to_the_full_text_without_requirements_section():
    extractor = make_extractor()

    text = "Backend developer working with Python and Docker."

    extractor.extract(text)

    assert extractor.skill_extractor.received == text
