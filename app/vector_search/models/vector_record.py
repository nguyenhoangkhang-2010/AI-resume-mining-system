from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class VectorRecord:
    """
    Generic vector representation.

    Supported entities:
    - candidate
    - job
    - skill
    - occupation
    - certification
    - knowledge entity
    """

    id: str

    vector: np.ndarray

    entity_type: str

    metadata: dict[str, Any]