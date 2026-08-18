from app.extraction.skills.bootstrap import (
    build_skill_normalizer,
)


def test_skill_normalization_benchmark():

    normalizer = build_skill_normalizer()

    samples = {
        " PYTHON3 ": "python",
        "Python,": "python",
        "(Python)": "python",
        "PYTHON": "python",
        "python programming": "python",
        "js": "javascript",
        "JavaScript ES6": "javascript",
    }

    for raw, expected in samples.items():
        assert (
            normalizer.normalize(raw)
            == expected
        )