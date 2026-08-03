from app.matching.ranking.ranking_adapter import (
    RankingAdapter,
)


def test_build_score_map():

    results = [
        {
            "faiss_id": "c1",
            "similarity_score": 0.9,
        },
        {
            "faiss_id": "c2",
            "similarity_score": 0.8,
        },
    ]


    score_map = RankingAdapter().build_score_map(
        results
    )


    assert score_map["c1"] == 0.9
    assert score_map["c2"] == 0.8