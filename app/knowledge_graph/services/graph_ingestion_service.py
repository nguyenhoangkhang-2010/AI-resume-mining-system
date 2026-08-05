from app.knowledge_base.models.taxonomy_entry import (
    TaxonomyEntry,
)

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)

from app.knowledge_graph.services.node_factory import (
    GraphNodeFactory,
)

from app.knowledge_graph.pipelines.graph_enrichment_pipeline import (
    GraphEnrichmentPipeline,
)


class GraphIngestionService:
    """
    Loads external knowledge entries
    into graph storage.
    """

    def __init__(
        self,
        repository: GraphRepository,
        factory: GraphNodeFactory,
        enrichment_pipeline: GraphEnrichmentPipeline,
    ):
        self.repository = repository
        self.factory = factory
        self.enrichment_pipeline = enrichment_pipeline


    def ingest(
        self,
        entries: list[TaxonomyEntry],
    ) -> None:

        for entry in entries:

            node = self.factory.create_from_taxonomy(
                entry
            )

            node = self.enrichment_pipeline.process(
                node
            )

            self.repository.add_node(
                node
            )