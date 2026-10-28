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

    # Hybrid scoring: candidates are fetched widely from the vector
    # index, then kept only if their final 0-100 score reaches the minimum.
    retrieval_top_k: int = 50
    min_overall_score: float = 50.0
    
    semantic_weight: float = 1.0
    penalty_per_missing_skill: float = 0.0