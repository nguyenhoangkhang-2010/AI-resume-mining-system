import torch
from sentence_transformers import SentenceTransformer
from loguru import logger
from typing import Optional

from app.core.config.settings import settings


class EmbeddingModelSingleton:
    _instance: Optional['EmbeddingModelSingleton'] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModelSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing Embedding Model Singleton...")
        self.device = self._get_device()
        try:
            # Load model specified in settings (e.g., sentence-transformers/all-MiniLM-L6-v2)
            logger.info(f"Loading model '{settings.MODEL_NAME}' on device '{self.device}'...")
            self._model = SentenceTransformer(settings.MODEL_NAME, device=self.device)
            logger.success("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            raise RuntimeError("Model is not initialized.")
        return self._model