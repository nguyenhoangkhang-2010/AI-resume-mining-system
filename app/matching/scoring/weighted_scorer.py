from app.models.matching_weights import MatchingWeights


class WeightedScorer:
    """
    Combines multiple matching scores
    into a single weighted score.

    Components that are unavailable (None) are left out and the
    remaining weights are renormalised, so a job without listed
    skills is scored on semantic similarity alone instead of being
    penalised.
    """

    def __init__(
        self,
        weights: MatchingWeights | None = None,
    ):
        self.weights = (
            weights
            or MatchingWeights()
        )

    def calculate(
        self,
        skill_score: float | None,
        semantic_score: float | None,
        experience_score: float | None = None,
    ) -> float:

        base = self._base_score(
            skill_score,
            semantic_score,
        )

        if experience_score is None:
            return round(base, 2)

        experience_weight = self.weights.experience_weight

        score = (
            (1 - experience_weight) * base
            + experience_weight * experience_score
        )

        return round(score, 2)

    def _base_score(
        self,
        skill_score: float | None,
        semantic_score: float | None,
    ) -> float:

        weighted = []

        if skill_score is not None:
            weighted.append(
                (skill_score, self.weights.skill_weight)
            )

        if semantic_score is not None:
            weighted.append(
                (semantic_score, self.weights.semantic_weight)
            )

        total_weight = sum(
            weight for _, weight in weighted
        )

        if total_weight == 0:
            return 0.0

        return sum(
            score * weight for score, weight in weighted
        ) / total_weight
