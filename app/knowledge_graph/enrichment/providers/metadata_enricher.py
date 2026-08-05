from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.base_enricher import (
    GraphEnricher,
)


class MetadataEnricher(GraphEnricher):
    """
    Basic graph enrichment implementation.

    This provider only demonstrates
    the enrichment pipeline.

    Future providers may use:
    - LLM
    - embeddings
    - external knowledge sources
    """

    def enrich(
        self,
        node: Node,
    ) -> Node:

        properties = {
            **node.properties,
            "enriched": True,
        }

        return Node(
            id=node.id,
            name=node.name,
            type=node.type,
            properties=properties,
        )