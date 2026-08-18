from app.knowledge_graph.models.node import Node

from app.knowledge_graph.services.enrichment_service import (
    GraphEnrichmentService,
)


class GraphEnrichmentPipeline:
    """
    Pipeline responsible for graph node enrichment.
    """


    def __init__(
        self,
        enrichment_service: GraphEnrichmentService,
    ):
        self.enrichment_service = enrichment_service


    def run(
        self,
        node: Node,
    ) -> Node:

        return self.enrichment_service.enrich(
            node
        )