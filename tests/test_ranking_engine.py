from app.schemas.matching_schema import RankedCandidate
from app.schemas.candidate_schema import CandidateResponse

from app.matching.ranking.ranking_engine import RankingEngine


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

    similarity_engine = MockSimilarityEngine()
    recommendation_engine = MockRecommendationEngine()

    engine = RankingEngine(
        similarity_engine=similarity_engine,
        recommendation_engine=recommendation_engine,
    )

    assert engine.similarity_engine == similarity_engine
    assert engine.recommendation_engine == recommendation_engine