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
        skill_score: float | None,
        semantic_score: float | None,
        experience_score: float | None = None,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> MatchingScore:

        overall = self.scorer.calculate(
            skill_score,
            semantic_score,
            experience_score,
        )

        confidence = self.confidence.calculate(
            skill_score,
            semantic_score,
            experience_score,
        )

        explanation = self.explainer.generate(
            skill_score,
            semantic_score,
            overall,
            experience_score=experience_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

        return MatchingScore(
            candidate_id=candidate_id,
            job_id=job_id,
            skill_score=skill_score,
            semantic_score=semantic_score,
            experience_score=experience_score,
            matched_skills=list(matched_skills or []),
            missing_skills=list(missing_skills or []),
            overall_score=overall,
            confidence_score=confidence,
            explanation=explanation,
        )
