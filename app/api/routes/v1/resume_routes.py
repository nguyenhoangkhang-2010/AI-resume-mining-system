import shutil
import uuid
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb.connection import mongo_db
from app.schemas.resume_schema import (
    ResumeResponse,
    ResumeStatusResponse,
)

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from loguru import logger

from app.api.dependencies import get_resume_service
from app.core.constants.app_constants import ALLOWED_EXTENSIONS
from app.services.resume_service import ResumeService


router = APIRouter()

UPLOAD_DIR = Path("data/uploads")


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid file type. "
                f"Allowed extensions: {ALLOWED_EXTENSIONS}"
            ),
        )

    unique_filename = (
        f"{uuid.uuid4()}{file_ext}"
    )

    file_path = (
        UPLOAD_DIR / unique_filename
    )

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception:
        logger.exception(
            "Failed to save uploaded resume: {}",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file.",
        )

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
    "/{resume_id}/status",
    response_model=ResumeStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_resume_status(
    resume_id: str,
) -> ResumeStatusResponse:

    try:
        object_id = ObjectId(resume_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume_id.",
        )

    db = mongo_db.get_db()

    resume = db["resumes"].find_one(
        {
            "_id": object_id,
        }
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    upload_status = resume.get(
        "upload_status",
        "pending",
    )

    if upload_status not in {
        "pending",
        "processing",
        "processed",
        "failed",
    }:
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
    )