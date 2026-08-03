from app.matching.ranking.ranking_sorter import RankingSorter
from app.schemas.candidate_schema import CandidateResponse
from app.schemas.matching_schema import RankedCandidate


def create_candidate():

    return CandidateResponse(
        id="1",
        resume_id="resume",
        personal_info={},
        education=[],
        experience=[],
        skills=[],
    )


def test_sort_candidates():

    sorter = RankingSorter()

    candidates = [
        RankedCandidate(
            similarity_score=40,
            skill_gaps=[],
            candidate_profile=create_candidate(),
        ),
        RankedCandidate(
            similarity_score=90,
            skill_gaps=[],
            candidate_profile=create_candidate(),
        ),
        RankedCandidate(
            similarity_score=70,
            skill_gaps=[],
            candidate_profile=create_candidate(),
        ),
    ]

    results = sorter.sort(candidates)

    assert results[0].similarity_score == 90
    assert results[1].similarity_score == 70
    assert results[2].similarity_score == 40