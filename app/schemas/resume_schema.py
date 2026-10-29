from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ResumeStatus = Literal[
    "pending",
    "processing",
    "processed",
    "needs_review",
    "failed",
]


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