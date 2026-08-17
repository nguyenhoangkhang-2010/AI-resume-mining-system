from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    """
    Structured personal information extracted from a resume.
    """

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree_level: List[str] = Field(
        default_factory=list
    )
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[float] = None


class Experience(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # ExperienceExtractor returns description as a list of bullet
    # points / sentences, not a single string. Keep this in sync with
    # whatever shape ExperienceExtractor._parse_result actually
    # produces.
    description: List[str] = Field(
        default_factory=list
    )

    employment_type: Optional[str] = None
    location: Optional[str] = None

    achievements: List[str] = Field(
        default_factory=list
    )


class Project(BaseModel):
    # Field names below match ProjectExtractor's output exactly
    # (see ProjectExtractor.EXTRACTION_PROMPT / _parse_result).
    # Keep this model in sync whenever the extractor's output shape
    # changes, otherwise Project.model_validate(...) will either
    # silently drop fields (if extra fields are ignored) or raise a
    # ValidationError (if a field's type doesn't match), which can
    # abort building the whole candidate document.
    title: Optional[str] = None
    description: List[str] = Field(
        default_factory=list
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    role: Optional[str] = None
    team_size: Optional[int] = None
    technologies: List[str] = Field(
        default_factory=list
    )
    responsibilities: List[str] = Field(
        default_factory=list
    )
    achievements: List[str] = Field(
        default_factory=list
    )
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


class Certification(BaseModel):
    # Generic shape; tighten this once CertificationExtractor's exact
    # output schema is confirmed. Using Dict[str, Any] passthrough
    # here would be even safer against future field-name drift, but
    # explicit fields make the schema self-documenting.
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


class CandidateModel(BaseModel):

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

    education: List[Education] = Field(
        default_factory=list,
        description="Structured educational experiences.",
    )

    experience: List[Experience] = Field(
        default_factory=list,
        description="List of work experiences.",
    )

    projects: List[Project] = Field(
        default_factory=list,
        description="Projects extracted from the resume.",
    )

    certifications: List[Certification] = Field(
        default_factory=list,
        description="Certifications extracted from the resume.",
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
            "collection_name": "candidates",
        }