from abc import ABC, abstractmethod

from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge


class GraphRepository(ABC):

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


    @abstractmethod
    def get_nodes_by_relation(
        self,
        node_id: str,
        relation: str,
    ) -> list[Node]:
        pass
    
    @abstractmethod
    def get_outgoing_edges(
        self,
        node_id: str,
    ) -> list[Edge]:
        pass