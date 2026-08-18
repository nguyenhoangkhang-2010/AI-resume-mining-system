from app.extraction.skills.statistics.extraction_statistics import (
    ExtractionStatistics,
)
from app.models.skill_match import SkillMatch


def test_statistics():

    stats = ExtractionStatistics()

    result = stats.summarize(
        [
            SkillMatch(
                "Python",
                1.0,
                "exact",
            ),
            SkillMatch(
                "FastAPI",
                0.95,
                "alias",
            ),
            SkillMatch(
                "React",
                0.81,
                "semantic",
            ),
        ]
    )

    assert result["total"] == 3
    assert result["sources"]["exact"] == 1
    assert result["sources"]["alias"] == 1
    assert result["sources"]["semantic"] == 1