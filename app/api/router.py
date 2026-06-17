from fastapi import APIRouter
from app.api.routes.v1 import resume_routes, job_routes, matching_routes

api_router = APIRouter()

api_router.include_router(resume_routes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(job_routes.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(matching_routes.router, prefix="/matches", tags=["Matching"])