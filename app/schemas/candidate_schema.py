from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.personal_info import PersonalInfo


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
    education: List[Dict[str, Any]] = Field(default_factory=list, description="List of educational backgrounds")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="List of work experiences")
    skills: List[str] = Field(default_factory=list, description="List of extracted skills")
    normalized_skills: List[str] = Field(
        default_factory=list,
        description="List of normalized canonical skills",
    )

    class Config:
        from_attributes = True
        populate_by_name = True