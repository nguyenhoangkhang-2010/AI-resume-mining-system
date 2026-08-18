from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResumeStatus = Literal[
    "pending",
    "processing",
    "processed",
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