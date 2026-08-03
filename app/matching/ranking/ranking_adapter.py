from typing import List, Dict, Any


class RankingAdapter:
    """
    Converts raw retrieval results
    into ranking-friendly format.
    """

    def build_score_map(
        self,
        retrieval_results: List[Dict[str, Any]],
    ) -> Dict[str, float]:

        return {
            item["faiss_id"]: item["similarity_score"]
            for item in retrieval_results
        }