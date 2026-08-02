from app.extraction.skills.benchmark.benchmark import (
    SkillExtractionBenchmark,
)
from app.extraction.skills.skill_extractor import (
    SkillExtractor,
)


def test_benchmark():

    benchmark = SkillExtractionBenchmark()

    extractor = SkillExtractor()

    result = benchmark.measure(
        extractor,
        "Python FastAPI"
    )

    assert "skills" in result
    assert "elapsed_seconds" in result
    assert result["elapsed_seconds"] >= 0