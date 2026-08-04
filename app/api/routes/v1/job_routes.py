from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_job_service

from app.schemas.job_schema import JobCreateRequest, JobResponse
from app.services.job_service import JobService

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    job_service: JobService = Depends(
        get_job_service,
    ),
):
    return job_service.create_job(request)