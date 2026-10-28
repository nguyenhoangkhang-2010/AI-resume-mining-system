from app.matching.scoring.experience_scorer import (
    ExperienceCalculator,
    ExperienceScorer,
)
from app.matching.scoring.skill_overlap_scorer import SkillOverlapScorer
from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)
from app.models.matching_score import MatchingScore


class HybridCandidateScorer:
    """
    Scores one candidate against a job by combining skill coverage,
    semantic similarity and experience through the hybrid strategy.
    """

    def __init__(
        self,
        strategy=None,
        skill_scorer=None,
        experience_calculator=None,
        experience_scorer=None,
    ):
        self.strategy = strategy or HybridMatchingStrategy()
        self.skill_scorer = skill_scorer or SkillOverlapScorer()
        self.experience_calculator = (
            experience_calculator or ExperienceCalculator()
        )
        self.experience_scorer = experience_scorer or ExperienceScorer()

    def score(
        self,
        job,
        candidate,
        semantic_score: float,
    ) -> MatchingScore:

        required_skills = (
            getattr(job, "normalized_skills", None)
            or job.required_skills
        )

        candidate_skills = [
            *(getattr(candidate, "normalized_skills", None) or []),
            *(candidate.skills or []),
        ]

        overlap = self.skill_scorer.score(
            required_skills,
            candidate_skills,
        )

        candidate_years = self.experience_calculator.total_years(
            getattr(candidate, "experience", None)
        )

        experience_score = self.experience_scorer.score(
            getattr(job, "experience_years", None),
            candidate_years,
        )

        return self.strategy.match(
            candidate_id=str(
                getattr(candidate, "id", None)
                or getattr(candidate, "resume_id", "")
            ),
            job_id=str(getattr(job, "id", None) or ""),
            skill_score=overlap.score,
            semantic_score=semantic_score,
            experience_score=experience_score,
            matched_skills=overlap.matched,
            missing_skills=overlap.missing,
        )
