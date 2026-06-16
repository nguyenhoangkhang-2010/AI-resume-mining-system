from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, description="The job title (e.g., Senior Data Engineer)")
    description: str = Field(..., min_length=10, description="The full job description text")


class JobResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the job")
    title: str = Field(..., description="The job title")
    required_skills: List[str] = Field(default_factory=list, description="AI-extracted required skills")
    created_at: datetime = Field(..., description="Timestamp of job creation")

    class Config:
        from_attributes = True