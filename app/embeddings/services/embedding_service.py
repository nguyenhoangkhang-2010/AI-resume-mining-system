import time
import numpy as np
from typing import List
from loguru import logger

from app.embeddings.models.embedding_model import EmbeddingModelSingleton


class EmbeddingService:
    
    def __init__(self):
        self.model_loader = EmbeddingModelSingleton()
        self.model = self.model_loader.model

    def generate_embedding(self, text: str) -> np.ndarray:
        logger.debug(f"Generating embedding for single text of length {len(text)}")
        start_time = time.time()
        
        try:
            # Normalizing embeddings is crucial for cosine similarity
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
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