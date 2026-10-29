from fastapi import APIRouter
from app.api.routes.v1 import (
    candidate_routes,
    job_routes,
    matching_routes,
    recommendation_routes,
    resume_routes,
    search_routes,
)

api_router = APIRouter()

api_router.include_router(resume_routes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(job_routes.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(candidate_routes.router, prefix="/candidates", tags=["Candidates"])
api_router.include_router(matching_routes.router, prefix="/matches", tags=["Matching"])
api_router.include_router(search_routes.router, prefix="/search", tags=["Search"])
api_router.include_router(
    recommendation_routes.router, prefix="/recommendations", tags=["Recommendations"]
)
