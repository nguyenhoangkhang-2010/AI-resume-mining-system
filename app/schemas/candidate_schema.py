from pydantic import BaseModel, Field
from typing import List, Dict, Any


class CandidateResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the candidate document")
    resume_id: str = Field(..., description="Reference ID to the original resume")
    personal_info: Dict[str, Any] = Field(default_factory=dict, description="Extracted personal details")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="List of educational backgrounds")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="List of work experiences")
    skills: List[str] = Field(default_factory=list, description="List of extracted skills")
    

    class Config:
        from_attributes = True
        populate_by_name = True