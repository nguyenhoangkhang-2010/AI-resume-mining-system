import threading
import time
from collections import OrderedDict

import numpy as np
from typing import List, Optional
from loguru import logger

from app.core.config.settings import settings

from app.embeddings.models.embedding_model import EmbeddingModelSingleton

class _EmbeddingCache:
    """
    The vectors of recently embedded texts (least recently used first out).

    Matching embeds the job text on every request, and that is most of the
    time of the request (about 120 of 180 ms on the development CPU); the
    same job is matched again whenever someone reloads the page. The vector
    of a text never changes while the model stays the same.
    """

    def __init__(self) -> None:
        self._entries: "OrderedDict[str, np.ndarray]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, text: str) -> Optional[np.ndarray]:
        with self._lock:
            vector = self._entries.get(text)

            if vector is not None:
                self._entries.move_to_end(text)

            # A copy, so a caller that changes the vector cannot change the cache.
            return None if vector is None else vector.copy()

    def put(self, text: str, vector: np.ndarray) -> None:
        size = settings.EMBEDDING_CACHE_SIZE

        if size <= 0:
            return

        with self._lock:
            self._entries[text] = vector.copy()
            self._entries.move_to_end(text)

            while len(self._entries) > size:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


embedding_cache = _EmbeddingCache()


class EmbeddingService:
    
    def __init__(self):
        self.model_loader = EmbeddingModelSingleton()
        self.model = self.model_loader.model

    def generate_embedding(self, text: str) -> np.ndarray:
        cached = embedding_cache.get(text)

        if cached is not None:
            return cached

        logger.debug(f"Generating embedding for single text of length {len(text)}")
        start_time = time.time()
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            embedding_cache.put(text, embedding)
            elapsed_time = time.time() - start_time
            logger.debug(f"Successfully generated single embedding in {elapsed_time:.3f}s")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            logger.warning("Empty text list provided for batch embeddings.")
            return np.array([])

        logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
        start_time = time.time()
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            elapsed_time = time.time() - start_time
            logger.success(f"Successfully generated {len(texts)} embeddings in {elapsed_time:.3f}s")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encoder interface used by ProfileEmbedder: normalised vectors,
        one row per text.
        """
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)

        return self.generate_batch_embeddings(texts)
