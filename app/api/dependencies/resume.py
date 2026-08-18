from fastapi import Request

from app.services.resume_service import ResumeService


def get_resume_service(
    request: Request,
) -> ResumeService:
    return request.app.state.resume_service