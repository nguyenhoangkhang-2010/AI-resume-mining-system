from typing import Optional

from pydantic import BaseModel, Field


class RankingMetadata(BaseModel):

    total_candidates: int = Field(
        ...,
        description="Total candidates received for ranking"
    )

    ranked_candidates: int = Field(
        ...,
        description="Number of candidates after ranking"
    )

    filtered_candidates: int = Field(
        ...,
        description="Number of candidates removed by ranking filter"
    )

    similarity_threshold: float = Field(
        ...,
        description=(
            "Threshold used during ranking: a cosine similarity (0-1) "
            "in similarity mode, a minimum overall score (0-100) in hybrid mode"
        )
    )

    scoring_mode: Optional[str] = Field(
        default=None,
        description="Scoring mode used for this ranking, e.g. 'hybrid'"
    )