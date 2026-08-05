from app.knowledge_graph.models.node import Node

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)


class GraphService:
    """
    Service layer for graph node operations.
    """

    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository


    def add_node(
        self,
        node: Node,
    ) -> None:

        self.repository.add_node(
            node
        )


    def get_node(
        self,
        node_id: str,
    ) -> Node | None:

        return self.repository.get_node(
            node_id
        )