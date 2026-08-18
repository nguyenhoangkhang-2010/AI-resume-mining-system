from unittest.mock import Mock

from app.job_processing.pipelines.job_pipeline import (
    JobPipeline,
)


def test_job_pipeline():

    pipeline = JobPipeline()

    pipeline.parser.parse = Mock(
        return_value="""
Software Engineer

Requirements

Python
FastAPI
Docker

Responsibilities

Develop APIs
Write tests
"""
    )

    result = pipeline.process(
        "job.txt"
    )

    assert "Python" in result["requirements"]

    assert "Develop APIs" in result["responsibilities"]

    assert isinstance(
        result["skills"],
        list,
    )
    
def test_empty_job_description():
    pipeline = JobPipeline()
    
    pipeline.parser.parse = Mock(
        return_value=""
    )
    
    result = pipeline.process("job.txt")

    assert result == {
        "requirements": None,
        "responsibilities": None,
        "skills": [],
    }