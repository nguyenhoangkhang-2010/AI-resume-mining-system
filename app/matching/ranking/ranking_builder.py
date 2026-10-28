from app.schemas.candidate_schema import CandidateResponse
from app.schemas.matching_schema import RankedCandidate


class RankingBuilder:

    def build(
        self,
        candidate,
        similarity_score,
        skill_gaps,
        score_breakdown=None,
    ) -> RankedCandidate:

        return RankedCandidate(
            similarity_score=similarity_score,
            skill_gaps=skill_gaps,
            score_breakdown=score_breakdown,
            candidate_profile=CandidateResponse.model_validate(
                candidate
            ),
        )
