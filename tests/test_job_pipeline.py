from unittest.mock import Mock

from app.job_processing.pipelines.job_pipeline import (
    JobPipeline,
)


def test_job_pipeline():

    pipeline = JobPipeline()

    pipeline.parser.extract_text = Mock(
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

    assert "requirements" in result
    assert "responsibilities" in result
    assert "skills" in result