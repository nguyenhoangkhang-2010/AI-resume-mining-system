from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResumeModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    filename: str
    file_path: str
    upload_status: str = Field(default="pending", description="Status can be pending, processed, or failed")
    raw_text: Optional[str] = Field(default=None, description="Extracted raw text from the resume")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True