from fastapi import APIRouter, Depends, HTTPException

from app.services.matching_service import MatchingService
from app.api.dependencies.matching import get_matching_service


router = APIRouter()


@router.get(
    "/{job_id}",
    summary="Rank candidates for a job",
)
def rank_candidates(
    job_id: str,
    matching_service: MatchingService = Depends(get_matching_service),
):

    try:
        result = matching_service.match_candidates_for_job(
            job_id=job_id
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to rank candidates.",
        )