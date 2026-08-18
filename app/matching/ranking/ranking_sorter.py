from app.schemas.matching_schema import RankedCandidate


class RankingSorter:
    """
    Responsible for sorting ranked candidates.
    """

    def sort(
        self,
        candidates: list[RankedCandidate],
    ) -> list[RankedCandidate]:

        return sorted(
            candidates,
            key=lambda candidate: candidate.similarity_score,
            reverse=True,
        )