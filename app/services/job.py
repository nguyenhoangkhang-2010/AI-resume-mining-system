from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.schemas.job_schema import JobCreateRequest, JobResponse
from app.services.job_service import JobService

router = APIRouter()
job_service = JobService()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(request: JobCreateRequest):
    try:
        return job_service.create_job(request)
    except Exception as e:
        logger.error(f"Error in create_job endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))