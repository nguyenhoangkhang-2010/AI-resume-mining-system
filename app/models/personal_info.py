from datetime import datetime
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class Experience(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class CandidateModel(BaseModel):
    """
    Pydantic model for representing a candidate document in MongoDB.
    """

    id: Optional[str] = Field(
        default=None,
        alias="_id",
    )

    resume_id: str = Field(
        ...,
        description="The MongoDB ObjectId of the associated resume document.",
    )

    personal_info: PersonalInfo = Field(
        default_factory=PersonalInfo,
        description="Structured personal information extracted from the resume.",
    )

    skills: List[str] = Field(
        default_factory=list,
        description="List of skills extracted from the resume.",
    )

    normalized_skills: List[str] = Field(
        default_factory=list,
        description="List of normalized skills.",
    )

    education: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of educational experiences.",
    )

    experience: List[Experience] = Field(
        default_factory=list,
        description="List of work experiences.",
    )

    faiss_id: int = Field(
        ...,
        description="The ID used in the FAISS vector index.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "collection_name": "candidates"
        }