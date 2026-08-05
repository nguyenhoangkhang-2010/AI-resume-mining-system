from abc import ABC, abstractmethod

from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge


class GraphRepository(ABC):
    """
    Abstract graph storage interface.

    Future implementations:
    - In-memory graph
    - Neo4j
    - PostgreSQL graph extension
    - RDF store
    """

    @abstractmethod
    def add_node(
        self,
        node: Node
    ) -> None:
        pass


    @abstractmethod
    def add_edge(
        self,
        edge: Edge
    ) -> None:
        pass


    @abstractmethod
    def get_edges(
        self,
    ) -> list[Edge]:
        pass