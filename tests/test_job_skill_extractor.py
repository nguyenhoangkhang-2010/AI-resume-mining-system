from app.extraction.job.job_skill_extractor import (
    JobSkillExtractor,
)


def test_job_skill_extraction():

    text = """
Software Engineer

Requirements

Python
FastAPI
Docker
Git
PostgreSQL
"""

    extractor = JobSkillExtractor()

    result = extractor.extract(text)

    assert isinstance(result, list)

    assert "Python" in result
    assert "FastAPI" in result
    assert "Docker" in result
    assert "Git" in result
    assert "PostgreSQL" in result