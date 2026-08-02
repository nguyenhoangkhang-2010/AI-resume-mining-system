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