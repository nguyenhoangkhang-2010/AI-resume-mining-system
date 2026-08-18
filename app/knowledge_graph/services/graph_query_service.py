from app.knowledge_graph.models.node import Node
from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)


class GraphQueryService:
    """
    Generic graph query service.

    Does not contain domain knowledge.
    """

    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository


    def find_related_nodes(
        self,
        node_id: str,
        relation: str,
    ) -> list[Node]:

        return self.repository.get_nodes_by_relation(
            node_id,
            relation,
        )