from app.schemas.candidate_schema import CandidateResponse
from app.schemas.matching_schema import RankedCandidate


class RankingBuilder:

    def build(
        self,
        candidate,
        similarity_score,
        skill_gaps,
    ) -> RankedCandidate:

        return RankedCandidate(
            similarity_score=similarity_score,
            skill_gaps=skill_gaps,
            candidate_profile=CandidateResponse.model_validate(
                candidate
            ),
        )