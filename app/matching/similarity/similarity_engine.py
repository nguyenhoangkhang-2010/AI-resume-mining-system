from loguru import logger


class SimilarityEngine:    
    @staticmethod
    def normalize_score(raw_score: float) -> float:
        clamped_score = max(0.0, min(1.0, float(raw_score)))
        normalized = round(clamped_score * 100, 2)
        return normalized