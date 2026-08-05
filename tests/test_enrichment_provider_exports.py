from app.knowledge_graph.enrichment.providers import (
    GraphEnrichmentProvider,
    LLMProvider,
    HuggingFaceLLMProvider,
)


def test_provider_exports():

    assert GraphEnrichmentProvider is not None

    assert LLMProvider is not None

    assert HuggingFaceLLMProvider is not None