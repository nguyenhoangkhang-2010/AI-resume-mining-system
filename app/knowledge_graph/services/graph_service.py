from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge
from app.knowledge_graph.repositories.graph_repository import GraphRepository


class GraphService:
    """
    Application service for graph operations.
    """

    def __init__(
        self,
        repository: GraphRepository
    ):
        self.repository = repository


    def create_node(
        self,
        node: Node
    ) -> None:

        self.repository.add_node(node)


    def create_edge(
        self,
        edge: Edge
    ) -> None:

        self.repository.add_edge(edge)