from pydantic import BaseModel, Field
from typing import List
from app.schemas.candidate_schema import CandidateResponse


class RankedCandidate(BaseModel):
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    skill_gaps: List[str] = Field(default_factory=list, description="Required job skills missing from candidate")
    candidate_profile: CandidateResponse = Field(..., description="Full structured profile of the matched candidate")


class MatchResponse(BaseModel):
    job_id: str = Field(..., description="The ID of the job being matched")
    results: List[RankedCandidate] = Field(default_factory=list, description="Ranked list of candidates")

    class Config:
        from_attributes = True