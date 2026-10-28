from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.providers.llm_enricher import (
    LLMGraphEnricher,
)


from app.knowledge_graph.enrichment.prompt_builder import (
    PromptBuilder,
)


class FakeLLMProvider:

    def generate(
        self,
        prompt,
    ):
        return {
            "summary": "AI generated"
        }



def test_llm_graph_enricher():


    node = Node(
        id="skill_1",
        name="Python",
        type="skill",
        properties={}
    )


    enricher = LLMGraphEnricher(
        provider=FakeLLMProvider(),
        prompt_builder=PromptBuilder(),
    )


    result = enricher.enrich(
        node
    )


    assert (
        "llm_metadata"
        in result.properties
    )