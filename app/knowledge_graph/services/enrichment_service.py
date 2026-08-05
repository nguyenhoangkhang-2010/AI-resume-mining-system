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



class GraphEnrichmentService:
    """
    Coordinates graph enrichment.

    Domain agnostic.
    """


    def __init__(
        self,
        provider: GraphEnrichmentProvider,
    ):
        self.provider = provider


    def enrich(
        self,
        node: Node,
    ) -> Node:

        return self.provider.enrich(
            node
        )