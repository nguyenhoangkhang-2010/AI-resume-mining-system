from app.knowledge_graph.enrichment.registry.provider_registry import (
    ProviderRegistry,
)


class FakeProvider:

    def enrich(self, node):
        return node



def test_provider_registry():

    registry = ProviderRegistry()


    provider = FakeProvider()


    registry.register(
        "fake",
        provider,
    )


    result = registry.get(
        "fake"
    )


    assert result is provider


    assert "fake" in registry.available()