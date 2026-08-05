from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.base_enricher import (
    GraphEnricher,
)


class GraphEnrichmentService:
    """
    Executes graph enrichment pipeline.
    """


    def __init__(
        self,
        enricher: GraphEnricher,
    ):
        self.enricher = enricher


    def enrich(
        self,
        node: Node,
    ) -> Node:

        return self.enricher.enrich(
            node
        )