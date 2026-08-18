from typing import Dict

from app.knowledge_graph.enrichment.providers.base_provider import (
    GraphEnrichmentProvider,
)


class ProviderRegistry:
    """
    Registry for graph enrichment providers.

    Allows dynamic provider selection
    without changing pipeline logic.
    """


    def __init__(self):

        self._providers: Dict[
            str,
            GraphEnrichmentProvider
        ] = {}


    def register(
        self,
        name: str,
        provider: GraphEnrichmentProvider,
    ) -> None:

        self._providers[name] = provider


    def get(
        self,
        name: str,
    ) -> GraphEnrichmentProvider:

        if name not in self._providers:
            raise ValueError(
                f"Unknown enrichment provider: {name}"
            )

        return self._providers[name]


    def available(
        self,
    ) -> list[str]:

        return list(
            self._providers.keys()
        )