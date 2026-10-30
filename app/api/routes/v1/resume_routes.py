import uuid
from pathlib import Path

from typing import Optional

from app.database.mongodb.connection import mongo_db
from app.schemas.page import Page
from app.schemas.resume_schema import (
    ResumeDetail,
    ResumeListItem,
    ResumeResponse,
    ResumeStatus,
    ResumeStatusResponse,
)

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from loguru import logger

from app.api.dependencies import get_resume_catalog_service, get_resume_service
from app.api.pagination import PageParams, page_params
from app.api.security import heavy_rate_limit, require_admin
from app.core.config.settings import settings
from app.core.constants.app_constants import ALLOWED_EXTENSIONS
from app.core.exceptions import AppError, NotFoundError, UnsupportedFileTypeError
from app.core.identifiers import parse_object_id
from app.services.resume_catalog_service import KNOWN_STATUSES, ResumeCatalogService
from app.services.upload_validation import save_upload
from app.services.resume_service import ResumeService


router = APIRouter()

UPLOAD_DIR = Path("data/uploads")


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(heavy_rate_limit)],
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resume_service: ResumeService = Depends(
        get_resume_service,
    ),
):

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    file_ext = Path(
        file.filename
    ).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            "Invalid file type. "
            f"Allowed extensions: {sorted(ALLOWED_EXTENSIONS)}"
        )

    unique_filename = (
        f"{uuid.uuid4()}{file_ext}"
    )

    file_path = (
        UPLOAD_DIR / unique_filename
    )

    try:
        save_upload(
            file.file,
            file_path,
            file_ext,
            settings.MAX_UPLOAD_MB * 1024 * 1024,
        )

    except AppError:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to save uploaded resume: {}",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file.",
        ) from exc

    finally:
        await file.close()

    logger.info(
        "Resume uploaded successfully: {}",
        file.filename,
    )

    resume = resume_service.create_resume(
        file_path=str(file_path),
        filename=file.filename,
    )

    background_tasks.add_task(
        resume_service.process_resume,
        resume.id,
    )

    logger.info(
        "Resume {} queued for background processing.",
        resume.id,
    )

    return ResumeResponse.model_validate(
        resume
    )
    
@router.get(
    "/",
    response_model=Page[ResumeListItem],
)
def list_resumes(
    status_filter: Optional[ResumeStatus] = Query(
        default=None,
        alias="status",
        description="Only resumes in this processing status",
    ),
    page: PageParams = Depends(page_params),
    catalog: ResumeCatalogService = Depends(get_resume_catalog_service),
):
    return catalog.list_resumes(status_filter, page.limit, page.offset)


@router.get(
    "/{resume_id}",
    response_model=ResumeDetail,
)
def get_resume(
    resume_id: str,
    catalog: ResumeCatalogService = Depends(get_resume_catalog_service),
):
    return catalog.get_resume(resume_id)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_resume(
    resume_id: str,
    catalog: ResumeCatalogService = Depends(get_resume_catalog_service),
):
    catalog.delete_resume(resume_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{resume_id}/status",
    response_model=ResumeStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_resume_status(
    resume_id: str,
) -> ResumeStatusResponse:

    object_id = parse_object_id(resume_id, "Resume")

    db = mongo_db.get_db()

    resume = db["resumes"].find_one(
        {
            "_id": object_id,
        }
    )

    if not resume:
        raise NotFoundError(f"Resume not found: {resume_id}")

    upload_status = resume.get(
        "upload_status",
        "pending",
    )

    if upload_status not in KNOWN_STATUSES:
        logger.warning(
            "Unknown resume status '{}' for resume {}. "
            "Falling back to 'pending'.",
            upload_status,
            resume_id,
        )

        upload_status = "pending"

    return ResumeStatusResponse(
        resume_id=str(resume["_id"]),
        status=upload_status,
        reason=resume.get("status_reason"),
        warnings=resume.get("warnings") or [],
    )
