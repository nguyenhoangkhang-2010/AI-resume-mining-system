from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_candidate_service,
    get_job_recommendation_service,
)
from app.api.security import heavy_rate_limit
from app.api.pagination import PageParams, page_params
from app.schemas.candidate_schema import CandidateResponse, CandidateSummary
from app.schemas.job_match_schema import JobMatchResponse
from app.schemas.page import Page
from app.services.candidate_service import CandidateService
from app.services.job_recommendation_service import JobRecommendationService

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


@router.get(
    "/{candidate_id}/jobs",
    response_model=JobMatchResponse,
    dependencies=[Depends(heavy_rate_limit)],
)
def recommend_jobs(
    candidate_id: str,
    top_k: int = Query(default=10, ge=1, le=50, description="Jobs to return"),
    min_score: Optional[float] = Query(
        default=None,
        ge=0,
        le=100,
        description="Leave out jobs scoring below this (default: the matching minimum, 50)",
    ),
    location: Optional[str] = Query(
        default=None,
        max_length=120,
        description="Only jobs whose location contains this text (case-insensitive)",
    ),
    service: JobRecommendationService = Depends(get_job_recommendation_service),
):
    """Jobs that fit this candidate, best first, with the reasons."""

    return service.recommend_for_candidate(candidate_id, top_k, min_score, location)
