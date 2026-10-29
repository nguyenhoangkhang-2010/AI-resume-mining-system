from fastapi import APIRouter, Depends

from app.api.dependencies import get_candidate_search_service
from app.schemas.search_schema import (
    CandidateSearchRequest,
    CandidateSearchResponse,
)
from app.services.candidate_search_service import CandidateSearchService

router = APIRouter()


@router.post("/candidates", response_model=CandidateSearchResponse)
def search_candidates(
    request: CandidateSearchRequest,
    search_service: CandidateSearchService = Depends(get_candidate_search_service),
):
    return search_service.search(request.query, request.top_k)
