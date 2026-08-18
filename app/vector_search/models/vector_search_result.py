from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VectorSearchResult:

    id: str

    score: float

    entity_type: str

    metadata: Dict[str, Any]