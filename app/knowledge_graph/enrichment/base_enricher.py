from abc import ABC, abstractmethod

from app.knowledge_graph.models.node import Node


class GraphEnricher(ABC):
    """
    Abstract graph enrichment interface.

    Implementations can enrich nodes using:
    - rules
    - external knowledge sources
    - LLM
    """


    @abstractmethod
    def enrich(
        self,
        node: Node,
    ) -> Node:
        pass