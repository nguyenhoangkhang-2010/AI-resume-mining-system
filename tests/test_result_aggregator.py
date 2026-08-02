from app.extraction.skills.aggregation.result_aggregator import (
    ResultAggregator,
)

from app.models.skill_match import SkillMatch


def test_result_aggregator_keeps_highest_confidence():

    aggregator = ResultAggregator()

    matches = [

        SkillMatch(
            "Python",
            1.0,
            "exact",
        ),

        SkillMatch(
            "Python",
            0.95,
            "alias",
        ),

        SkillMatch(
            "React",
            0.9,
            "semantic",
        ),
    ]

    result = aggregator.aggregate(matches)

    assert len(result) == 2

    python = next(
        x for x in result
        if x.skill == "Python"
    )

    assert python.confidence == 1.0

    assert python.source == "exact"