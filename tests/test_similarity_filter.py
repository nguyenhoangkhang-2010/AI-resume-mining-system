from app.vector_search.filters.similarity_filter import (
    SimilarityFilter,
)

from app.vector_search.models.vector_search_result import (
    VectorSearchResult,
)


def test_similarity_filter():

    filter = SimilarityFilter(
        threshold=0.5
    )

    results = [
        VectorSearchResult(
            id="1",
            score=0.9,
            entity_type="candidate",
            metadata={}
        ),
        VectorSearchResult(
            id="2",
            score=0.2,
            entity_type="candidate",
            metadata={}
        ),
    ]


    filtered = filter.filter(results)


    assert len(filtered) == 1

    assert filtered[0].id == "1"