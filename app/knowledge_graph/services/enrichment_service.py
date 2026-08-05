from app.knowledge_graph.models.node import Node
from app.knowledge_graph.enrichment.providers.base_provider import (
    GraphEnrichmentProvider,
)


class GraphEnrichmentService:

    def __init__(
        self,
        provider: GraphEnrichmentProvider,
    ):
        self.provider = provider


    def enrich(
        self,
        node: Node,
    ) -> Node:

        return self.provider.enrich(node)