from app.schemas.job_schema import (
    JobCreateRequest,
    JobResponse,
)

from datetime import datetime


def test_job_create_request():

    request = JobCreateRequest(
        title="Backend Engineer",
        description="Python FastAPI Docker"
    )

    assert request.title == "Backend Engineer"


def test_job_response():

    response = JobResponse(
        id="1",
        title="Backend Engineer",
        required_skills=["Python"],
        created_at=datetime.utcnow(),
    )

    assert response.required_skills == ["Python"]