from app.services.resume_service import ResumeService


def get_resume_service() -> ResumeService:
    return ResumeService()