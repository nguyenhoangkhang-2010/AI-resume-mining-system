from app.knowledge_graph.models.node import Node

from app.knowledge_graph.services.enrichment_service import (
    GraphEnrichmentService,
)


class GraphEnrichmentPipeline:
    """
    Executes graph node enrichment workflow.

    Keeps enrichment workflow separated
    from ingestion logic.
    """

    def __init__(
        self,
        enrichment_service: GraphEnrichmentService,
    ):
        self.enrichment_service = enrichment_service


    def process(
        self,
        node: Node,
    ) -> Node:

        return self.enrichment_service.enrich(
            node
        )