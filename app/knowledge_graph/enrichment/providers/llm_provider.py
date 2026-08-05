from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract LLM provider.

    Responsible for generating
    knowledge enrichment information.
    """


    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        pass