from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CandidateModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    resume_id: str = Field(..., description="Reference to the Resume Document ID")
    personal_info: Dict[str, Any] = Field(default_factory=dict)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    faiss_id: Optional[int] = Field(default=None, description="Index ID mapped to the FAISS Vector Store")

    class Config:
        populate_by_name = True