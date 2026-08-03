from app.matching.confidence.confidence_calculator import (
    ConfidenceCalculator,
)


def test_confidence_calculation():

    confidence = (
        ConfidenceCalculator.calculate(
            skill_score=90,
            semantic_score=80,
        )
    )

    assert confidence == 85.0