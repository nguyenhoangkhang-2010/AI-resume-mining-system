from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ResumeStatus = Literal[
    "pending",
    "processing",
    "processed",
    "needs_review",
    "failed",
]


class ConfidenceInfo(BaseModel):
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "How far the extraction can be trusted, 0 to 1. Not a probability: "
            "see docs/evaluation/confidence.md"
        ),
    )
    level: Literal["low", "medium", "high"]
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="completeness, structure, extraction and fields, each 0 to 1",
    )
    sections: Dict[str, float] = Field(
        default_factory=dict,
        description="How surely each section was found, 0 to 1",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Short codes for what lowered the score (for example read_by_ocr)",
    )

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> Optional["ConfidenceInfo"]:
        stored = document.get("confidence")

        if not isinstance(stored, dict):
            return None

        try:
            return cls.model_validate(stored)
        except ValueError:
            return None


class ResumeResponse(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the resume document",
    )
    filename: str = Field(
        ...,
        description="Original name of the uploaded file",
    )
    upload_status: ResumeStatus = Field(
        ...,
        description="Current processing status of the resume",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp of when the resume was uploaded",
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class ResumeStatusResponse(BaseModel):
    resume_id: str = Field(
        ...,
        description="Unique identifier of the resume",
    )
    status: ResumeStatus = Field(
        ...,
        description="Current processing status of the resume",
    )
    reason: Optional[str] = Field(
        default=None,
        description=(
            "Why the resume is in needs_review or failed, as a short code "
            "(for example no_text_extracted, unreadable_file)"
        ),
    )
    warnings: List[str] = Field(
        default_factory=list,
        description=(
            "Things that could not be found in a processed resume "
            "(for example no_experience_found)"
        ),
    )
    confidence: Optional[ConfidenceInfo] = Field(
        default=None,
        description="Absent until the resume has been processed",
    )


class ResumeListItem(BaseModel):
    id: str
    filename: str
    status: ResumeStatus
    reason: Optional[str] = Field(
        default=None,
        description="Why the resume is in needs_review or failed, as a short code",
    )
    warnings: List[str] = Field(default_factory=list)
    confidence: Optional[ConfidenceInfo] = None
    created_at: datetime


class ResumeDetail(ResumeListItem):
    candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate created from this resume, if it was indexed",
    )
