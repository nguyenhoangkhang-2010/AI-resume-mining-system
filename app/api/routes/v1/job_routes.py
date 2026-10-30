from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_job_service
from app.api.pagination import PageParams, page_params
from app.api.security import heavy_rate_limit, require_admin
from app.schemas.job_schema import JobCreateRequest, JobResponse, JobSummary
from app.schemas.page import Page
from app.services.job_service import JobService

router = APIRouter()


# These handlers are plain functions on purpose: they do blocking work
# (MongoDB, text extraction), which FastAPI then runs in a worker thread
# instead of stalling the event loop.


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(heavy_rate_limit)],
)
def create_job(
    request: JobCreateRequest,
    job_service: JobService = Depends(
        get_job_service,
    ),
):
    return job_service.create_job(request)


@router.get("/", response_model=Page[JobSummary])
def list_jobs(
    page: PageParams = Depends(page_params),
    job_service: JobService = Depends(get_job_service),
):
    return job_service.list_jobs(page.limit, page.offset)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
):
    return job_service.get_job_response(job_id)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
):
    job_service.delete_job(job_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
