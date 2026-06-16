from pydantic import BaseModel, Field
from datetime import datetime


class ResumeResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the resume document")
    filename: str = Field(..., description="Original name of the uploaded file")
    upload_status: str = Field(..., description="Current processing status (e.g., pending, processed)")
    created_at: datetime = Field(..., description="Timestamp of when the resume was uploaded")

    class Config:
        from_attributes = True
        populate_by_name = True