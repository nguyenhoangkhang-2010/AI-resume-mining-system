from functools import lru_cache

from app.services.job_service import JobService


@lru_cache(maxsize=1)
def get_job_service() -> JobService:
    return JobService()
