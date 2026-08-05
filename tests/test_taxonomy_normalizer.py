from app.knowledge_base.services.taxonomy_normalizer import (
    TaxonomyNormalizer,
)


def test_normalize_lowercase():

    normalizer = TaxonomyNormalizer()

    result = normalizer.normalize(
        "Python"
    )

    assert result == "python"


def test_normalize_whitespace():

    normalizer = TaxonomyNormalizer()

    result = normalizer.normalize(
        "  Python   Programming "
    )

    assert result == "python programming"


def test_normalize_special_character():

    normalizer = TaxonomyNormalizer()

    result = normalizer.normalize(
        "C++ Programming"
    )

    assert result == "c programming"