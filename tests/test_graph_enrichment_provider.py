from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.providers.metadata_enricher import (
    MetadataEnricher,
)


def test_metadata_enricher():

    node = Node(
        id="node_1",
        name="Example",
        type="entity",
    )


    enricher = MetadataEnricher()


    result = enricher.enrich(
        node
    )


    assert result.id == "node_1"

    assert result.properties[
        "enriched"
    ] is True