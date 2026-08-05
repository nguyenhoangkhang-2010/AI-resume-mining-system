from app.knowledge_graph.models.node import Node
from app.knowledge_graph.enrichment.base_enricher import GraphEnricher


class SimpleGraphEnricher(GraphEnricher):

    def enrich(
        self,
        node: Node,
    ) -> Node:

        node.properties["enriched"] = True

        return node