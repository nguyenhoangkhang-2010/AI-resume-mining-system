from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_recommendation_service
from app.api.security import heavy_rate_limit
from app.schemas.recommendation_schema import SkillRecommendations
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get(
    "/",
    response_model=SkillRecommendations,
    dependencies=[Depends(heavy_rate_limit)],
)
def get_recommendations(
    job_id: str = Query(..., description="Job the candidate is compared with"),
    candidate_id: str = Query(..., description="Candidate to give recommendations to"),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    return recommendation_service.recommend(job_id, candidate_id)
