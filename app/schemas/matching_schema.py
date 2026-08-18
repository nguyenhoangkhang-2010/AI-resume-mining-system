from typing import List

from pydantic import BaseModel, Field

from app.schemas.ranking_schema import RankingMetadata
from app.schemas.ranked_candidate_schema import RankedCandidate


class MatchResponse(BaseModel):
    job_id: str
    results: List[RankedCandidate] = Field(
        default_factory=list
    )
    metadata: RankingMetadata
    class Config:
        from_attributes = True