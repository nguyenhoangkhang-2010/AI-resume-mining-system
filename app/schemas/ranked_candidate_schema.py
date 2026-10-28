from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.candidate_schema import CandidateResponse


class ScoreBreakdown(BaseModel):

    skill_score: Optional[float] = Field(
        default=None,
        description="Share of the job's required skills the candidate covers (0-100)"
    )

    semantic_score: Optional[float] = Field(
        default=None,
        description="Semantic similarity between job and candidate (0-100)"
    )

    experience_score: Optional[float] = Field(
        default=None,
        description="Candidate experience versus the job requirement (0-100)"
    )

    confidence_score: float = Field(
        default=0.0,
        description="Average of the available component scores (0-100)"
    )

    matched_skills: List[str] = Field(
        default_factory=list,
        description="Required skills the candidate has"
    )

    explanation: Dict[str, str] = Field(
        default_factory=dict,
        description="Human-readable explanation of each score component"
    )


class RankedCandidate(BaseModel):

    similarity_score: float = Field(
        ...,
        description="Final match score used for ranking"
    )

    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Missing skills"
    )

    score_breakdown: Optional[ScoreBreakdown] = Field(
        default=None,
        description="Per-component scores; present when hybrid scoring is used"
    )

    candidate_profile: CandidateResponse


    class Config:
        from_attributes = True
