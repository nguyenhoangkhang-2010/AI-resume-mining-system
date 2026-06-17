import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.embeddings.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_embedding_model():
    with patch("app.embeddings.services.embedding_service.EmbeddingModelSingleton") as MockSingleton:
        mock_instance = MockSingleton.return_value
        mock_instance.model = MagicMock()
        yield mock_instance

def test_generate_embedding(mock_embedding_model):
    mock_array = np.array([0.1, 0.2, 0.3])
    mock_embedding_model.model.encode.return_value = mock_array
    
    service = EmbeddingService()
    result = service.generate_embedding("Test text")
    
    assert isinstance(result, np.ndarray)
    assert result.tolist() == [0.1, 0.2, 0.3]
    mock_embedding_model.model.encode.assert_called_once()

def test_generate_batch_embeddings(mock_embedding_model):
    mock_array = np.array([[0.1, 0.2], [0.3, 0.4]])
    mock_embedding_model.model.encode.return_value = mock_array
    
    service = EmbeddingService()
    result = service.generate_batch_embeddings(["Text 1", "Text 2"])
    assert isinstance(result, np.ndarray)

def test_generate_batch_embeddings_empty(mock_embedding_model):
    service = EmbeddingService()
    result = service.generate_batch_embeddings([])
    assert result.size == 0