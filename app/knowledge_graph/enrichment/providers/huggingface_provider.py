from transformers import pipeline

from app.core.config.settings import settings

from app.knowledge_graph.enrichment.providers.llm_provider import (
    LLMProvider,
)


class HuggingFaceLLMProvider(
    LLMProvider,
):

    def __init__(
        self,
        model_name: str | None = None,
    ):

        self.generator = pipeline(
            task="text-generation",
            model=model_name
            or settings.LLM_MODEL_NAME,
            token=settings.hf_token,
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        result = self.generator(
            prompt,
            max_new_tokens=settings.MAX_NEW_TOKENS,
            do_sample=False,
        )

        return result[0]["generated_text"]