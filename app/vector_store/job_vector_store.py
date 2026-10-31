"""
The vector index of jobs.

It is a second FAISS index, separate from the candidate index, so a search for
jobs never returns candidates and the two can be rebuilt independently. The
vectors have the same dimension and are compared by cosine similarity.
"""

import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
from loguru import logger

from app.core.config.settings import settings
from app.database.vector_db.faiss_manager import FaissManager


_managers: Dict[str, FaissManager] = {}
_managers_lock = threading.Lock()


def shared_manager(path: Path) -> FaissManager:
    """
    One manager per index file for the whole process. Two managers on the
    same file would each keep their own copy in memory and overwrite each
    other's changes (the service that creates jobs and the one that searches
    them are separate objects).
    """

    key = str(Path(path).resolve())

    with _managers_lock:
        if key not in _managers:
            _managers[key] = FaissManager.for_path(
                Path(path), save_every=settings.FAISS_SAVE_EVERY
            )

        return _managers[key]


class JobVectorStore:

    def __init__(self, manager: Optional[FaissManager] = None) -> None:
        self._manager = manager

    @property
    def manager(self) -> FaissManager:
        if self._manager is None:
            self._manager = shared_manager(Path(settings.JOB_FAISS_INDEX_PATH))

        return self._manager

    def add(self, faiss_id: int, embedding: np.ndarray) -> None:
        self.manager.add_vector(faiss_id, embedding)

    def remove(self, faiss_id: int) -> bool:
        try:
            return self.manager.remove_ids([faiss_id]) > 0
        except Exception as exc:
            logger.error("Could not remove job vector {}: {}", faiss_id, exc)
            return False

    def indexed_ids(self) -> Set[int]:
        return self.manager.ids()

    def replace_all(self, faiss_ids: List[int], embeddings: np.ndarray) -> None:
        self.manager.replace_all(np.asarray(faiss_ids), embeddings)

    def flush(self) -> None:
        self.manager.flush()

    def search(self, query: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Jobs most similar to the query vector: faiss_id and cosine score."""

        distances, indices = self.manager.search(query, top_k=top_k)

        return [
            {"faiss_id": int(faiss_id), "similarity_score": float(score)}
            for score, faiss_id in zip(distances, indices)
            if faiss_id != -1 and score > 0
        ]
