from pydantic import BaseModel, Field


class GraphEntity(BaseModel):
    """
    Base entity for knowledge graph objects.

    Graph entities are intentionally generic because
    ontology definitions are data-driven.
    """

    id: str = Field(
        description="Unique identifier"
    )

    name: str = Field(
        description="Human readable name"
    )