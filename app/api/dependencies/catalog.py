from functools import lru_cache

from app.services.candidate_search_service import CandidateSearchService
from app.services.candidate_service import CandidateService
from app.services.recommendation_service import RecommendationService
from app.services.resume_catalog_service import ResumeCatalogService


@lru_cache(maxsize=1)
def get_resume_catalog_service() -> ResumeCatalogService:
    from app.vector_store.vector_store import VectorStore

    return ResumeCatalogService(VectorStore())


@lru_cache(maxsize=1)
def get_candidate_service() -> CandidateService:
    return CandidateService()


@lru_cache(maxsize=1)
def get_candidate_search_service() -> CandidateSearchService:
    from app.embeddings.services.embedding_service import EmbeddingService
    from app.vector_store.vector_store import VectorStore

    return CandidateSearchService(EmbeddingService(), VectorStore())


@lru_cache(maxsize=1)
def get_recommendation_service() -> RecommendationService:
    from app.matching.recommendation.recommendation_engine import (
        RecommendationEngine,
    )

    return RecommendationService(RecommendationEngine())
