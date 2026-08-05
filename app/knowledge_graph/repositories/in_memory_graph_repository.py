from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)


class InMemoryGraphRepository(GraphRepository):
    """
    Temporary graph storage.

    Used for development and testing.
    Can later be replaced by:
    - Neo4j
    - Graph database
    - RDF store
    """

    def __init__(self):

        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []


    def add_node(
        self,
        node: Node,
    ) -> None:

        self._nodes[node.id] = node


    def add_edge(
        self,
        edge: Edge,
    ) -> None:

        self._edges.append(edge)


    def get_node(
        self,
        node_id: str,
    ) -> Node | None:

        return self._nodes.get(node_id)


    def get_all_nodes(
        self,
    ) -> list[Node]:

        return list(
            self._nodes.values()
        )