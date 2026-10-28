import os

import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Optional, Tuple

from app.core.config.settings import settings
from app.core.constants.app_constants import EMBEDDING_DIMENSION


class FaissManager:
    _instance: Optional['FaissManager'] = None
    _index: Optional[faiss.Index] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaissManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing FAISS Manager Singleton...")
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.dimension = EMBEDDING_DIMENSION
        self._load_or_create_index()

    def _load_or_create_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.index_path.exists():
            logger.info(f"Loading existing FAISS index from {self.index_path}")
            try:
                self._index = faiss.read_index(str(self.index_path))
                logger.success(f"Loaded FAISS index with {self._index.ntotal} vectors.")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                raise
        else:
            logger.info("Creating new FAISS index (IndexFlatIP for Cosine Similarity)")
            base_index = faiss.IndexFlatIP(self.dimension)
            self._index = faiss.IndexIDMap(base_index)
            logger.success("Created new FAISS index.")

    def save_index(self):
        temporary_path = self.index_path.with_suffix(".tmp")

        try:
            # Write beside the target and swap, so a crash mid-write cannot
            # leave a truncated index behind.
            faiss.write_index(self._index, str(temporary_path))
            os.replace(temporary_path, self.index_path)
            logger.debug(f"FAISS index saved successfully to {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise

    def replace_all(self, ids: np.ndarray, vectors: np.ndarray):
        """
        Replaces the whole index with the given vectors (used when the
        embedding text changes and every vector must be rebuilt).
        """
        ids = np.asarray(ids, dtype=np.int64)
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have the same length")

        if len(set(ids.tolist())) != len(ids):
            raise ValueError("faiss ids must be unique")

        index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))

        if len(ids):
            faiss.normalize_L2(vectors)
            index.add_with_ids(vectors, ids)

        self._index = index
        self.save_index()

    def add_vector(self, faiss_id: int, embedding: np.ndarray):
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)  # Normalize vector for exact Cosine Similarity
        ids = np.array([faiss_id], dtype=np.int64)
        
        try:
            self._index.add_with_ids(vector, ids)
            logger.debug(f"Added vector with ID {faiss_id} to FAISS.")
            self.save_index()
        except Exception as e:
            logger.error(f"Error adding vector to FAISS: {e}")
            raise

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        if self._index.ntotal == 0:
            logger.warning("FAISS index is empty. Cannot perform search.")
            return np.array([]), np.array([])
            
        vector = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(vector)  # Normalize query for exact Cosine Similarity
        try:
            distances, indices = self._index.search(vector, top_k)
            return distances[0], indices[0]
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            raise