from app.knowledge_graph.models.node import Node

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)


class GraphTraversalService:
    """
    Generic graph traversal service.

    Responsible for navigating graph structure.

    Does not contain ontology knowledge.
    """


    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository



    def traverse(
        self,
        start_node_id: str,
        depth: int = 1,
    ) -> list[Node]:
        visited: set[str] = set()
        result: list[Node] = []
        self._walk(
            node_id=start_node_id,
            depth=depth,
            visited=visited,
            result=result,
        )
        return result


    def _walk(
        self,
        node_id: str,
        depth: int,
        visited: set[str],
        result: list[Node],
    ) -> None:
        if depth <= 0:
            return
        if node_id in visited:
            return
        visited.add(node_id)
        edges = self.repository.get_outgoing_edges(
            node_id
        )
        for edge in edges:
            node = self.repository.get_node(
                edge.target
            )
            if node is None:
                continue
            result.append(node)
            self._walk(
                node_id=edge.target,
                depth=depth - 1,
                visited=visited,
                result=result,
            )