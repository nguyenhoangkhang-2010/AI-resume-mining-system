from app.api.dependencies import (
    get_job_service,
    get_matching_service,
    get_resume_service,
)

from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.resume_service import ResumeService


def test_get_job_service():
    assert isinstance(get_job_service(), JobService)


def test_get_resume_service():
    assert isinstance(get_resume_service(), ResumeService)


def test_get_matching_service():
    assert isinstance(get_matching_service(), MatchingService)