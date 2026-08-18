from app.matching.ranking.ranking_builder import RankingBuilder
from app.models.candidate import CandidateModel


def test_build_ranked_candidate():

    candidate = CandidateModel(
        id="c1",
        resume_id="resume_001",
        personal_info={
            "name": "Test Candidate",
            "email": "test@gmail.com",
        },
        education=[],
        experience=[],
        skills=[],
        faiss_id=1,
    )

    ranked = RankingBuilder().build(
        candidate=candidate,
        similarity_score=85,
        skill_gaps=["Docker"],
    )

    assert ranked.similarity_score == 85
    assert ranked.skill_gaps == ["Docker"]