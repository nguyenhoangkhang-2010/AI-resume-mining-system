from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.ranked_candidate_schema import ScoreBreakdown


class JobMatch(BaseModel):
    job_id: str
    title: str
    location: Optional[str] = None
    occupation: Optional[str] = None
    experience_years: Optional[int] = Field(
        default=None, description="Years of experience the job asks for"
    )
    required_skills: List[str] = Field(default_factory=list)

    score: float = Field(
        ..., description="How well the candidate fits the job (0-100), used for ordering"
    )
    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Required skills the candidate's profile does not show",
    )
    score_breakdown: ScoreBreakdown = Field(
        description="Per-component scores, matched skills and explanations"
    )


class JobMatchMetadata(BaseModel):
    retrieved: int = Field(
        ..., description="Jobs found by the vector search before filtering"
    )
    ranked: int = Field(..., description="Jobs returned")
    below_min_score: int = Field(
        ..., description="Retrieved jobs left out because their score was under min_score"
    )
    outside_location: int = Field(
        ..., description="Retrieved jobs left out by the location filter"
    )
    unindexed_jobs: int = Field(
        ...,
        description=(
            "Jobs that have no vector yet and so cannot be recommended "
            "(run scripts/reindex_jobs.py)"
        ),
    )
    min_score: float
    scoring_mode: str = "hybrid"


class JobMatchResponse(BaseModel):
    candidate_id: str
    results: List[JobMatch] = Field(default_factory=list)
    metadata: JobMatchMetadata
