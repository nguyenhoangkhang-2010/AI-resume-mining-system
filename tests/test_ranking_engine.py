from app.schemas.matching_schema import RankedCandidate
from app.schemas.candidate_schema import CandidateResponse

from app.matching.ranking.ranking_engine import RankingEngine

from unittest.mock import Mock


class MockSimilarityEngine:

    def normalize_score(self, score):
        return 100


class MockRecommendationEngine:

    def analyze_skill_gaps(
        self,
        required_skills,
        candidate_skills,
    ):
        return ["Python"]


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
    
def test_ranking_engine_dependency_injection():

    ranking_adapter = Mock()
    ranking_sorter = Mock()
    ranking_pipeline = Mock()

    engine = RankingEngine(
        ranking_adapter=ranking_adapter,
        ranking_sorter=ranking_sorter,
        ranking_pipeline=ranking_pipeline,
    )

    assert engine.ranking_adapter is ranking_adapter
    assert engine.ranking_sorter is ranking_sorter
    assert engine.ranking_pipeline is ranking_pipeline