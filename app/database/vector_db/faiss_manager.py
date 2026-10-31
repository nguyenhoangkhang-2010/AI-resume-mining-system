import os
import threading

import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Iterable, Optional, Set, Tuple

from app.core.config.settings import settings
from app.core.constants.app_constants import EMBEDDING_DIMENSION


class FaissManager:
    """
    Owns the FAISS index.

    Every operation takes one re-entrant lock, because FAISS indexes are
    not safe for concurrent writes or for searching while another thread
    modifies them, and uploads are processed on a thread pool.

    The index is persisted after every `save_every` changes (1 = after each
    change). A larger value saves write time on big indexes at the cost of
    losing at most that many vectors on a crash; the MongoDB candidates are
    the source of truth and `scripts/check_index_consistency.py` repairs the
    difference.
    """

    _instance: Optional['FaissManager'] = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                logger.info("Initializing FAISS Manager Singleton...")
                instance = object.__new__(cls)
                instance._configure(
                    Path(settings.FAISS_INDEX_PATH),
                    EMBEDDING_DIMENSION,
                    settings.FAISS_SAVE_EVERY,
                )
                cls._instance = instance

        return cls._instance

    @classmethod
    def for_path(
        cls,
        index_path: Path,
        dimension: int = EMBEDDING_DIMENSION,
        save_every: int = 1,
    ) -> 'FaissManager':
        """A separate, non-singleton manager (used by tools and tests)."""
        instance = object.__new__(cls)
        instance._configure(Path(index_path), dimension, save_every)

        return instance

    @classmethod
    def shutdown(cls) -> None:
        """Persists pending changes if the singleton was ever created."""
        if cls._instance is not None:
            cls._instance.flush()

    def _configure(self, index_path: Path, dimension: int, save_every: int):
        self.index_path = index_path
        self.dimension = dimension
        self.save_every = max(1, int(save_every))
        self._lock = threading.RLock()
        self._unsaved_changes = 0
        self._index: faiss.Index
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

    @property
    def ntotal(self) -> int:
        with self._lock:
            return self._index.ntotal

    def ids(self) -> Set[int]:
        with self._lock:
            if self._index.ntotal == 0:
                return set()

            id_map = self._index.id_map  # type: ignore[attr-defined]

            return {int(i) for i in faiss.vector_to_array(id_map)}

    def save_index(self):
        with self._lock:
            temporary_path = self.index_path.with_suffix(".tmp")

            try:
                # Write beside the target and swap, so a crash mid-write
                # cannot leave a truncated index behind.
                faiss.write_index(self._index, str(temporary_path))
                os.replace(temporary_path, self.index_path)
                self._unsaved_changes = 0
                logger.debug(f"FAISS index saved successfully to {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to save FAISS index: {e}")
                raise

    def flush(self):
        with self._lock:
            if self._unsaved_changes:
                self.save_index()

    def _record_change(self):
        self._unsaved_changes += 1

        if self._unsaved_changes >= self.save_every:
            self.save_index()

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

        with self._lock:
            self._index = index
            self.save_index()

    def add_vector(self, faiss_id: int, embedding: np.ndarray):
        """
        Adds a vector, replacing any vector already stored under the same
        id so an id never appears twice in the index.
        """
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)  # Normalize vector for exact Cosine Similarity
        ids = np.array([faiss_id], dtype=np.int64)

        with self._lock:
            try:
                self._remove(ids)
                self._index.add_with_ids(vector, ids)
                logger.debug(f"Added vector with ID {faiss_id} to FAISS.")
                self._record_change()
            except Exception as e:
                logger.error(f"Error adding vector to FAISS: {e}")
                raise

    def _remove(self, ids: np.ndarray) -> int:
        # The faiss Python wrapper accepts a numpy int64 array here; the
        # type stubs only declare IDSelector.
        return int(self._index.remove_ids(ids))  # type: ignore[arg-type]

    def remove_ids(self, faiss_ids: Iterable[int]) -> int:
        ids = np.array(list(faiss_ids), dtype=np.int64)

        if not len(ids):
            return 0

        with self._lock:
            removed = self._remove(ids)

            if removed:
                self._record_change()

        return removed

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        with self._lock:
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
