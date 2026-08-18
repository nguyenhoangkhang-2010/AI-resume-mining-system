from app.extraction.skills.filters.confidence_filter import (
    ConfidenceFilter,
)
from app.models.skill_match import SkillMatch


def test_confidence_filter():

    filter = ConfidenceFilter(
        minimum_confidence=0.8
    )

    matches = [
        SkillMatch("Python",1.0,"exact"),
        SkillMatch("React",0.75,"semantic"),
    ]

    result = filter.filter(matches)

    assert len(result) == 1
    assert result[0].skill == "Python"