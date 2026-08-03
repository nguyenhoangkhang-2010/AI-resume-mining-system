from app.matching.ranking.ranking_config import (
    RankingConfig,
)

from app.core.constants.app_constants import (
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
)


def test_default_ranking_config():

    config = RankingConfig()

    assert config.similarity_threshold == SIMILARITY_THRESHOLD
    assert config.top_k == DEFAULT_TOP_K


def test_custom_ranking_config():

    config = RankingConfig(
        similarity_threshold=0.8,
        top_k=10,
    )

    assert config.similarity_threshold == 0.8
    assert config.top_k == 10