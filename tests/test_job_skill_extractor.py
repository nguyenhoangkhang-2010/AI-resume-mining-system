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

    assert "python" in result
    assert "fastapi" in result
    assert "docker" in result
    assert "git" in result
    assert "postgresql" in result