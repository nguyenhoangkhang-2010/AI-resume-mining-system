from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingWeights:
    """
    Configuration for weighting
    different matching components.
    """
    
    skill_weight: float = 0.6
    semantic_weight: float = 0.4