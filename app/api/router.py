from fastapi import APIRouter
from app.api.endpoints import resume, job, matching

api_router = APIRouter()

api_router.include_router(resume.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(job.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(matching.router, prefix="/matches", tags=["Matching"])