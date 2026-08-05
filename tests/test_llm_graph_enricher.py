from app.knowledge_graph.enrichment.providers.llm_enricher import (
    LLMGraphEnricher,
)

from app.knowledge_graph.models.node import Node



class FakeLLM:

    def generate(
        self,
        prompt,
    ):
        return "AI generated metadata"



def test_llm_enrichment():

    enricher = LLMGraphEnricher(
        FakeLLM()
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