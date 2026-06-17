import numpy as np
from loguru import logger
from typing import List, Dict, Any

from app.database.vector_db.faiss_manager import FaissManager
from app.core.constants.app_constants import DEFAULT_TOP_K


class VectorStore:
    def __init__(self):
        self.faiss_manager = FaissManager()

    def add_candidate_embedding(self, faiss_id: int, embedding: np.ndarray) -> bool:
        logger.info(f"Adding candidate embedding with FAISS ID {faiss_id} to vector store.")
        try:
            self.faiss_manager.add_vector(faiss_id, embedding)
            return True
        except Exception as e:
            logger.error(f"Failed to add candidate embedding to vector store: {e}")
            return False

    def search_similar_candidates(self, query_embedding: np.ndarray, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        logger.info(f"Searching for top {top_k} similar candidates in vector store.")
        
        distances, indices = self.faiss_manager.search(query_embedding, top_k=top_k)
        
        results = []
        for score, faiss_id in zip(distances, indices):
            if faiss_id != -1:
                results.append({
                    "faiss_id": int(faiss_id),
                    "similarity_score": float(score)
                })
                
        logger.info(f"Found {len(results)} valid matches.")
        return results