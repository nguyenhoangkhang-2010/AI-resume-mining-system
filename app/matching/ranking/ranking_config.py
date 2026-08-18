from dataclasses import dataclass

from app.core.constants.app_constants import (
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
)


@dataclass(frozen=True)
class RankingConfig:
    """
    Configuration for ranking process.
    """

    similarity_threshold: float = SIMILARITY_THRESHOLD
    top_k: int = DEFAULT_TOP_K
    
    semantic_weight: float = 1.0
    penalty_per_missing_skill: float = 0.0