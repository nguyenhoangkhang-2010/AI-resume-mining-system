from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    faiss_id: Optional[int] = Field(default=None, description="Index ID for Job vector in FAISS")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True