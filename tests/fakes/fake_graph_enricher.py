from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.base_enricher import (
    GraphEnricher,
)


class FakeGraphEnricher(GraphEnricher):

    def enrich(
        self,
        node: Node,
    ) -> Node:

        return Node(
            id=node.id,
            name=node.name,
            type=node.type,
            properties={
                **node.properties,
                "tested": True,
            },
        )