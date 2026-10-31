from functools import lru_cache

from app.services.job_recommendation_service import JobRecommendationService
from app.services.job_service import JobService


@lru_cache(maxsize=1)
def get_job_service() -> JobService:
    return JobService()


@lru_cache(maxsize=1)
def get_job_recommendation_service() -> JobRecommendationService:
    # One instance, so the embedding model and the job index are loaded once.
    return JobRecommendationService()
