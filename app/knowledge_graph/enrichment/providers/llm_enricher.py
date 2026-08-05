from app.knowledge_graph.models.node import Node

from app.knowledge_graph.enrichment.base_enricher import (
    GraphEnricher,
)

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)



class LLMGraphEnricher(
    GraphEnricher
):


    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider



    def enrich(
        self,
        node: Node,
    ) -> Node:


        prompt = f"""
        Analyze this knowledge entity:

        Name:
        {node.name}

        Type:
        {node.type}

        Return useful metadata.
        """


        response = self.provider.generate(
            prompt
        )


        node.properties[
            "llm_metadata"
        ] = response


        return node