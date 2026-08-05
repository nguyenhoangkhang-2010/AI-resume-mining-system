from typing import Any

from pydantic import BaseModel, Field


class Edge(BaseModel):
    """
    Generic relationship between graph nodes.
    """

    source: str = Field(
        description="Source node id"
    )

    target: str = Field(
        description="Target node id"
    )

    relation: str = Field(
        description="Ontology relationship type"
    )

    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional relationship metadata"
    )