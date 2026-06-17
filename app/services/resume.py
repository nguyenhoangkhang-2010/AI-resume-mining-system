import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from loguru import logger

from app.schemas.resume_schema import ResumeResponse
from app.services.resume_service import ResumeService
from app.core.constants.app_constants import ALLOWED_EXTENSIONS

router = APIRouter()
resume_service = ResumeService()

UPLOAD_DIR = Path("data/uploads")


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid file type. Allowed extensions: {ALLOWED_EXTENSIONS}"
        )

    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save file")

    try:
        response = resume_service.process_uploaded_resume(str(file_path), file.filename)
        return response
    except Exception as e:
        logger.error(f"Error processing resume in endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))