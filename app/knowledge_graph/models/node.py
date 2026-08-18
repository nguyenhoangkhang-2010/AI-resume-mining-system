from typing import Any

from pydantic import Field

from app.knowledge_graph.models.graph_entity import GraphEntity


class Node(GraphEntity):
    """
    Generic knowledge graph node.

    Node type is ontology-defined instead of
    being hardcoded in application code.
    """

    type: str = Field(
        description="Ontology entity type"
    )

    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional ontology properties"
    )