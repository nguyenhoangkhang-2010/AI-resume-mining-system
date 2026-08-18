from __future__ import annotations

from typing import Optional

import torch
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.core.config.settings import settings


class EmbeddingModelSingleton:
    _instance: Optional["EmbeddingModelSingleton"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls) -> "EmbeddingModelSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()

        return cls._instance

    def _initialize(self) -> None:
        logger.info(
            "Initializing multilingual embedding model..."
        )

        self.device = self._get_device()

        logger.info(
            "Loading embedding model '{}' on device '{}'",
            settings.MODEL_NAME,
            self.device,
        )

        try:
            self._model = SentenceTransformer(
                settings.MODEL_NAME,
                device=self.device,
            )

            logger.success(
                "Multilingual embedding model loaded successfully."
            )

        except Exception as exc:
            logger.exception(
                "Failed to load embedding model: {}",
                exc,
            )
            raise

    @staticmethod
    def _get_device() -> str:
        if torch.cuda.is_available():
            return "cuda"

        if (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ):
            return "mps"

        return "cpu"

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            raise RuntimeError(
                "Embedding model is not initialized."
            )

        return self._model