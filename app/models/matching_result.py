from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MatchingResultModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    job_id: str
    candidate_id: str
    similarity_score: float = Field(..., description="Cosine similarity score out of 1.0")
    skill_gaps: List[str] = Field(default_factory=list, description="List of skills required but missing from candidate")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True