from app.schemas.matching_schema import RankedCandidate
from app.schemas.candidate_schema import CandidateResponse


def create_candidate_profile():

    return CandidateResponse(
        id="c1",
        resume_id="resume_001",
        personal_info={
            "name": "Test Candidate",
            "email": "test@gmail.com",
        },
        education=[],
        experience=[],
        skills=[],
    )


def test_sort_candidates():

    candidates = [
        RankedCandidate(
            similarity_score=60,
            skill_gaps=[],
            candidate_profile=create_candidate_profile(),
        ),
        RankedCandidate(
            similarity_score=90,
            skill_gaps=[],
            candidate_profile=create_candidate_profile(),
        ),
        RankedCandidate(
            similarity_score=75,
            skill_gaps=[],
            candidate_profile=create_candidate_profile(),
        ),
    ]

    candidates.sort(
        key=lambda x: x.similarity_score,
        reverse=True
    )

    assert candidates[0].similarity_score == 90
    assert candidates[1].similarity_score == 75
    assert candidates[2].similarity_score == 60