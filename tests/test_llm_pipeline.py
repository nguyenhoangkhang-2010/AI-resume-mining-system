from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)

from app.knowledge_graph.enrichment.providers.llm_enricher import (
    LLMGraphEnricher,
)

from app.knowledge_graph.enrichment.prompt_builder import (
    PromptBuilder,
)


class FakeLLMProvider(
    LLMProvider,
):

    def generate(
        self,
        prompt: str,
    ) -> str:

        return "Generated metadata"


def test_llm_enrichment():

    enricher = LLMGraphEnricher(
        FakeLLMProvider(),
        PromptBuilder(),
    )

    node = Node(
        id="skill_python",
        name="Python",
        type="skill",
    )

    node = enricher.enrich(
        node
    )

    assert node.properties[
        "llm_metadata"
    ] == "Generated metadata"