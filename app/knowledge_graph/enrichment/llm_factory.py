from app.knowledge_graph.enrichment.providers.huggingface_provider import (
    HuggingFaceLLMProvider,
)

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)


class LLMProviderFactory:
    """
    Factory responsible for constructing
    LLM providers.

    Additional providers (OpenAI, Ollama,
    Gemini, Azure, etc.) can be added
    without changing the enrichment layer.
    """

    @staticmethod
    def huggingface(
        model_name: str,
    ) -> LLMProvider:

        return HuggingFaceLLMProvider(
            model_name=model_name,
        )