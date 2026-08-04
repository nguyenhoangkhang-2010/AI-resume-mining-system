from app.services.job_service import JobService


def get_job_service() -> JobService:
    return JobService()