from typing import List

from pydantic import BaseModel

from app.schemas.ranked_candidate_schema import RankedCandidate
from app.schemas.ranking_schema import RankingMetadata


class RankingResult(BaseModel):
    results: List[RankedCandidate]
    metadata: RankingMetadata
    class Config:
        from_attributes = True