from abc import ABC, abstractmethod

from app.knowledge_graph.models.node import Node


class GraphEnricher(ABC):
    """
    Base interface for graph enrichment.

    Implementations may use:
    - rules
    - external knowledge
    - LLM
    - embedding models
    """

    @abstractmethod
    def enrich(
        self,
        node: Node,
    ) -> Node:
        pass