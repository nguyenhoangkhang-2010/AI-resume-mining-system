from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_candidate_service
from app.api.pagination import PageParams, page_params
from app.schemas.candidate_schema import CandidateResponse, CandidateSummary
from app.schemas.page import Page
from app.services.candidate_service import CandidateService

router = APIRouter()


@router.get("/", response_model=Page[CandidateSummary])
def list_candidates(
    skill: Optional[str] = Query(
        default=None,
        description="Only candidates with this normalised skill (case-insensitive)",
    ),
    page: PageParams = Depends(page_params),
    candidate_service: CandidateService = Depends(get_candidate_service),
):
    return candidate_service.list_candidates(skill, page.limit, page.offset)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: str,
    candidate_service: CandidateService = Depends(get_candidate_service),
):
    return candidate_service.get_candidate(candidate_id)
