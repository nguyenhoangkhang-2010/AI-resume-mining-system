from typing import List
from pydantic import BaseModel


class RecommendationItem(BaseModel):
    type: str
    title: str
    priority: str
    source: str | None = None


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]

class SkillRecommendations(BaseModel):
    job_id: str
    candidate_id: str
    missing_skills: List[str]
    recommendations: List[RecommendationItem]
