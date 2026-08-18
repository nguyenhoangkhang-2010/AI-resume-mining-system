from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.providers.huggingface_provider import (
    HuggingFaceLLMProvider,
)

from app.knowledge_graph.enrichment.providers.llm_enricher import (
    LLMGraphEnricher,
)

from app.knowledge_graph.enrichment.prompt_builder import (
    PromptBuilder,
)


def test_llm_graph_enricher():

    provider = HuggingFaceLLMProvider()

    enricher = LLMGraphEnricher(
        provider=provider,
        prompt_builder=PromptBuilder(),
    )

    node = Node(
        id="1",
        name="Python",
        type="skill",
    )

    enriched = enricher.enrich(node)

    assert "llm_metadata" in enriched.properties

    assert len(
        enriched.properties["llm_metadata"]
    ) > 0