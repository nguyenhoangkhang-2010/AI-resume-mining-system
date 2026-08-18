from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    title: str = Field(..., description="The title of the job.")
    description: str = Field(..., description="The raw job description text.")


class JobResponse(BaseModel):
    id: str = Field(..., alias="_id", description="Unique identifier of the job document")
    title: str = Field(..., description="The title of the job.")
    description: str = Field(..., description="A concise summary of the job responsibilities and requirements.")
    raw_text: str = Field(..., description="The original raw text from the job description.")
    required_skills: List[str] = Field(default_factory=list, description="List of key technical and soft skills required.")
    normalized_skills: List[str] = Field(default_factory=list, description="List of normalized skills based on a taxonomy.")
    experience_years: Optional[int] = Field(None, description="Minimum years of experience required.")
    responsibilities: List[str] = Field(default_factory=list, description="List of main job responsibilities.")
    occupation: Optional[str] = Field(None, description="Normalized occupation from a taxonomy like O*NET.")
    created_at: datetime = Field(..., description="Timestamp of when the job was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the last update")

    class Config:
        from_attributes = True
        populate_by_name = True