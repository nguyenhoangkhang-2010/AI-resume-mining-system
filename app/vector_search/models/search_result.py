from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VectorSearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]