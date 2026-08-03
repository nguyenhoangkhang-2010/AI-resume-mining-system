from typing import List
from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    missing_skills: List[str]

class RecommendationItem(BaseModel):
    type: str
    title: str
    priority: str


class RecommendationResult(BaseModel):
    recommendations: List[RecommendationItem]