from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.schemas.matching_schema import MatchResponse
from app.services.matching_service import MatchingService

router = APIRouter()
matching_service = MatchingService()


@router.get("/{job_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def match_candidates(job_id: str):
    try:
        return matching_service.match_candidates_for_job(job_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))