from typing import List

from pydantic import BaseModel, Field

from app.schemas.candidate_schema import CandidateResponse


class RankedCandidate(BaseModel):

    similarity_score: float = Field(
        ...,
        description="Cosine similarity score"
    )

    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Missing skills"
    )

    candidate_profile: CandidateResponse


    class Config:
        from_attributes = True