from app.knowledge_base.models.taxonomy_entry import (
    TaxonomyEntry,
)

from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.services.node_factory import (
    GraphNodeFactory,
)

from app.knowledge_graph.services.graph_ingestion_service import (
    GraphIngestionService,
)

from app.knowledge_graph.services.enrichment_service import (
    GraphEnrichmentService,
)

from tests.fakes.fake_graph_enricher import (
    FakeGraphEnricher,
)


def test_ingest_taxonomy_entries():

    repo = InMemoryGraphRepository()

    factory = GraphNodeFactory()

    enrichment_service = GraphEnrichmentService(
        FakeGraphEnricher()
    )


    service = GraphIngestionService(
        repo,
        factory,
        enrichment_service,
    )


    entries = [
        TaxonomyEntry(
            id="entity_1",
            name="Entity One",
            category="knowledge",
            aliases=[],
        )
    ]


    service.ingest(
        entries
    )


    node = repo.get_node(
        "entity_1"
    )


    assert node is not None

    assert node.name == "Entity One"

    assert node.type == "knowledge"

    assert node.properties[
        "tested"
    ] is True