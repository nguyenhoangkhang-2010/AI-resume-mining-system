from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.providers.base_provider import (
    GraphEnrichmentProvider,
)

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)

from app.knowledge_graph.enrichment.prompt_builder import (
    PromptBuilder,
)


class LLMGraphEnricher(
    GraphEnrichmentProvider,
):

    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
    ):
        self.provider = provider
        self.prompt_builder = prompt_builder

    def enrich(
        self,
        node: Node,
    ) -> Node:

        prompt = self.prompt_builder.build(
            node
        )

        response = self.provider.generate(
            prompt
        )

        node.properties[
            "llm_metadata"
        ] = response

        return node