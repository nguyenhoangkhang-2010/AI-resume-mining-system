from app.matching.confidence.confidence_calculator import ConfidenceCalculator
from app.matching.explanation.explanation_engine import ExplanationEngine
from app.matching.scoring.weighted_scorer import WeightedScorer
from app.matching.strategies.matching_strategy import MatchingStrategy
from app.models.matching_score import MatchingScore


class HybridMatchingStrategy(MatchingStrategy):

    def __init__(self):
        self.scorer = WeightedScorer()
        self.confidence = ConfidenceCalculator()
        self.explainer = ExplanationEngine()

    def match(
        self,
        candidate_id: str,
        job_id: str,
        skill_score: float,
        semantic_score: float,
    ) -> MatchingScore:

        overall = self.scorer.calculate(
            skill_score,
            semantic_score,
        )

        confidence = self.confidence.calculate(
            skill_score,
            semantic_score,
        )

        explanation = self.explainer.generate(
            skill_score,
            semantic_score,
            overall,
        )

        return MatchingScore(
            candidate_id=candidate_id,
            job_id=job_id,
            skill_score=skill_score,
            semantic_score=semantic_score,
            overall_score=overall,
            confidence_score=confidence,
            explanation=explanation,
        )