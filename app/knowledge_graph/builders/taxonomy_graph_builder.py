from app.knowledge_base.models.taxonomy_entry import (
    TaxonomyEntry,
)

from app.knowledge_graph.builders.graph_builder import (
    GraphBuilder,
)

from app.knowledge_graph.services.node_factory import (
    GraphNodeFactory,
)

from app.knowledge_graph.services.enrichment_service import (
    GraphEnrichmentService,
)


class TaxonomyGraphBuilder(GraphBuilder):
    """
    Builds graph nodes from taxonomy entries.
    """


    def __init__(
        self,
        repository,
        factory: GraphNodeFactory,
        enrichment_service: GraphEnrichmentService,
    ):
        super().__init__(
            repository
        )

        self.factory = factory

        self.enrichment_service = enrichment_service


    def build(
        self,
        source: list[TaxonomyEntry],
    ) -> None:


        for entry in source:

            node = self.factory.create_from_taxonomy(
                entry
            )


            node = self.enrichment_service.enrich(
                node
            )


            self.repository.add_node(
                node
            )