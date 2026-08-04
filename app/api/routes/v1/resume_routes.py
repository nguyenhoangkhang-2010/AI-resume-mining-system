import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from app.api.dependencies import get_resume_service
from app.core.constants.app_constants import ALLOWED_EXTENSIONS
from app.schemas.resume_schema import ResumeResponse
from app.services.resume_service import ResumeService

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    resume_service: ResumeService = Depends(
        get_resume_service,
    ),
):
    """Upload a candidate's resume (PDF) to be processed and indexed."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid file type. Allowed extensions: {ALLOWED_EXTENSIONS}"
        )

    # Generate a unique filename to prevent overwrites and path traversal issues
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.exception("Failed to save uploaded file.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save file")

    return resume_service.process_uploaded_resume(
        str(file_path),
        file.filename,
    )