from abc import ABC, abstractmethod

from app.knowledge_graph.models.node import Node


class GraphEnrichmentProvider(ABC):
    """
    Abstract provider for graph enrichment.

    Implementations can use:
    - LLM
    - embedding models
    - external knowledge sources

    This layer does not contain domain knowledge.
    """


    @abstractmethod
    def enrich(
        self,
        node: Node,
    ) -> Node:
        pass