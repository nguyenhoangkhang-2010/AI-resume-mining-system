from app.matching.ranking.ranking_filter import RankingFilter


def test_accept():

    assert RankingFilter().accept(0.9)


def test_reject():

    assert not RankingFilter().accept(0.2)