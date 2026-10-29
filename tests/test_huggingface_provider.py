import pytest

from app.knowledge_graph.enrichment.providers.huggingface_provider import (
    HuggingFaceLLMProvider,
)


pytestmark = pytest.mark.slow


def test_huggingface_provider():

    provider = HuggingFaceLLMProvider()

    result = provider.generate(
        "What is Python?"
    )

    assert isinstance(result, str)

    assert len(result) > 0