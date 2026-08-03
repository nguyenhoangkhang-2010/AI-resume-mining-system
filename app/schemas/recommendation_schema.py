from typing import List
from pydantic import BaseModel


class RecommendationItem(BaseModel):
    type: str
    title: str
    priority: str


class RecommendationResult(BaseModel):
    recommendations: List[RecommendationItem]