from typing import Any

from pydantic import BaseModel, Field


class OntologyDefinition(BaseModel):
    """
    Defines a knowledge graph ontology entity.

    Example:
    skill
    occupation
    certification
    industry
    """

    name: str

    description: str | None = None

    properties: dict[str, Any] = Field(
        default_factory=dict
    )
    
class RelationshipTypes:
    REQUIRES_SKILL = "requires_skill"
    RELATED_TO = "related_to"
    BELONGS_TO = "belongs_to"
    PARENT_OF = "parent_of"