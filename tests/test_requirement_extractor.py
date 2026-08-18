from app.extraction.job.requirement_extractor import (
    RequirementExtractor,
)


def test_requirement_extraction():

    text = """
Software Engineer

Requirements

Python
FastAPI
Docker

Responsibilities

Develop APIs
"""

    extractor = RequirementExtractor()

    result = extractor.extract(text)

    assert "Python" in result
    assert "FastAPI" in result
    assert "Docker" in result