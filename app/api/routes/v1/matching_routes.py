from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_matching_service

from app.schemas.matching_schema import MatchResponse
from app.services.matching_service import MatchingService

router = APIRouter()


@router.get("/{job_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def match_candidates(
    job_id: str,
    matching_service: MatchingService = Depends(
        get_matching_service,
    ),
):
    return matching_service.match_candidates_for_job(
        job_id
    )