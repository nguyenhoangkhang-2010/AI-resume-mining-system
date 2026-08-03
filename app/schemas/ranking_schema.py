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
        description="Similarity threshold used during ranking"
    )