from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.candidate import (
    Certification,
    Education,
    Experience,
    PersonalInfo,
    Project,
)


class CandidateResponse(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the candidate document"
    )
    resume_id: str = Field(..., description="Reference ID to the original resume")
    personal_info: PersonalInfo = Field(
        default_factory=PersonalInfo,
        description="Extracted personal details"
    )
    education: List[Education] = Field(default_factory=list, description="List of educational backgrounds")
    experience: List[Experience] = Field(default_factory=list, description="List of work experiences")
    projects: List[Project] = Field(default_factory=list, description="List of projects")
    certifications: List[Certification] = Field(default_factory=list, description="List of certifications")
    skills: List[str] = Field(default_factory=list, description="List of extracted skills")
    normalized_skills: List[str] = Field(
        default_factory=list,
        description="List of normalized canonical skills",
    )

    class Config:
        from_attributes = True
        populate_by_name = True
