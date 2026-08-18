from app.knowledge_graph.models.edge import Edge
from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)
from app.knowledge_graph.ontology.definitions import (
    RelationshipTypes,
)


class HierarchyService:
    """
    Generic hierarchy relationship service.

    Works with ontology-defined relationships.
    Does not contain domain-specific entities.
    """

    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository


    def add_parent_relation(
        self,
        parent_id: str,
        child_id: str,
    ) -> None:

        edge = Edge(
            source=parent_id,
            target=child_id,
            relation=RelationshipTypes.PARENT_OF,
        )

        self.repository.add_edge(edge)