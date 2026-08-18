from app.extraction.job.responsibility_extractor import (
    ResponsibilityExtractor,
)


def test_responsibility_extraction():

    text = """
Software Engineer

Responsibilities

Develop REST APIs
Maintain backend services
Write unit tests

Benefits

Remote work
Health insurance
"""

    extractor = ResponsibilityExtractor()

    result = extractor.extract(text)

    assert result is not None
    assert "Develop REST APIs" in result
    assert "Maintain backend services" in result
    assert "Write unit tests" in result