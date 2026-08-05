from transformers import pipeline

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)


class HuggingFaceLLMProvider(
    LLMProvider
):

    def __init__(
        self,
        model_name: str,
    ):

        self.generator = pipeline(
            "text-generation",
            model=model_name,
        )


    def generate(
        self,
        prompt: str,
    ) -> str:

        result = self.generator(
            prompt,
            max_new_tokens=128,
        )


        return result[0]["generated_text"]