from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingWeights:
    """
    Configuration for weighting
    different matching components.

    skill_weight and semantic_weight are relative to each other.
    experience_weight is the share of the final score given to
    experience when the job states a requirement; the remaining
    share is split between skills and semantic similarity.
    """

    skill_weight: float = 0.6
    semantic_weight: float = 0.4
    experience_weight: float = 0.2
