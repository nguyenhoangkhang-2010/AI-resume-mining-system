from typing import List

from pydantic import BaseModel, Field

from app.schemas.candidate_schema import CandidateSummary


class CandidateSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Free text, for example a skill set or a job title",
    )
    top_k: int = Field(default=10, ge=1, le=50)


class CandidateSearchHit(BaseModel):
    candidate: CandidateSummary
    score: float = Field(
        ...,
        description="Semantic similarity between the query and the candidate (0-100)",
    )


class CandidateSearchResponse(BaseModel):
    query: str
    results: List[CandidateSearchHit] = Field(default_factory=list)
