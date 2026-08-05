from app.knowledge_graph.models.node import Node
from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry


class GraphNodeFactory:
    """
    Converts external knowledge entries
    into generic graph nodes.

    Does not contain domain mapping logic.
    """

    def create_from_taxonomy(
        self,
        entry: TaxonomyEntry,
    ) -> Node:

        return Node(
            id=entry.id,
            name=entry.name,
            type=entry.category,
            properties={
                "aliases": entry.aliases,
            },
        )