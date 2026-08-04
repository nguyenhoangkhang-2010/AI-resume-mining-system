from app.vector_search import (
    VectorSearchService,
    VectorSearchFactory,
    CandidateEmbeddingPipeline,
)


def test_vector_package_import():

    assert VectorSearchService is not None

    assert VectorSearchFactory is not None

    assert CandidateEmbeddingPipeline is not None