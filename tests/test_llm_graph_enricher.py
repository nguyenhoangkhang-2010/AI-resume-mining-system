from app.knowledge_graph.enrichment.providers.llm_enricher import (
    LLMGraphEnricher,
)

from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.prompt_builder import (
    PromptBuilder,
)


class FakeLLM:

    def generate(
        self,
        prompt,
    ):
        return "AI generated metadata"



def test_llm_enrichment():

    enricher = LLMGraphEnricher(
        provider=FakeLLM(),
        prompt_builder=PromptBuilder(),
    )


    node = Node(
        id="skill_1",
        type="skill",
        name="Python",
        properties={}
    )


    result = enricher.enrich(
        node
    )


    assert (
        result.properties[
            "llm_metadata"
        ]
        ==
        "AI generated metadata"
    )