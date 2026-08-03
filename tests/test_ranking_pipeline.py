from unittest.mock import Mock

from app.matching.ranking.ranking_pipeline import RankingPipeline
from app.schemas.ranking_result import RankingResult


class MockCandidate:

    def __init__(
        self,
        faiss_id,
        skills=None,
    ):
        self.faiss_id = faiss_id
        self.skills = skills or []


class MockJob:

    def __init__(
        self,
        required_skills=None,
    ):
        self.required_skills = required_skills or []


class MockRankingFilter:

    def __init__(self):
        self.config = Mock()
        self.config.similarity_threshold = 0.7

    def accept(self, score):
        return score >= 0.7


class MockSimilarityEngine:

    def normalize_score(self, score):
        return score


class MockRecommendationEngine:

    def analyze_skill_gaps(
        self,
        required_skills,
        candidate_skills,
    ):
        return [
            skill
            for skill in required_skills
            if skill not in candidate_skills
        ]


class MockRankingBuilder:

    def build(
        self,
        candidate,
        similarity_score,
        skill_gaps,
    ):
        return {
            "similarity_score": similarity_score,
            "skill_gaps": skill_gaps,
            "candidate_profile": {
                "resume_id": candidate.faiss_id,
                "skills": candidate.skills,
            },
        }


def test_ranking_pipeline_process():

    pipeline = RankingPipeline(
        similarity_engine=MockSimilarityEngine(),
        recommendation_engine=MockRecommendationEngine(),
        ranking_filter=MockRankingFilter(),
        ranking_scorer=MockRankingScorer(),
        ranking_builder=MockRankingBuilder(),
    )

    job = MockJob(
        required_skills=[
            "Python",
            "SQL",
        ]
    )

    candidates = [
        MockCandidate(
            faiss_id="1",
            skills=[
                "Python",
                "SQL",
            ],
        ),
        MockCandidate(
            faiss_id="2",
            skills=[
                "Python",
            ],
        ),
        MockCandidate(
            faiss_id="3",
            skills=[
                "Java",
            ],
        ),
    ]

    score_map = {
        "1": 0.9,
        "2": 0.8,
        "3": 0.5,
    }


    result = pipeline.process(
        job=job,
        candidates=candidates,
        score_map=score_map,
    )


    assert isinstance(
        result,
        RankingResult,
    )


    assert len(result.results) == 2


    assert result.metadata.total_candidates == 3

    assert result.metadata.ranked_candidates == 2

    assert result.metadata.filtered_candidates == 1

    assert result.metadata.similarity_threshold == 0.7
    
class MockRankingScorer:

    def calculate(
        self,
        similarity_score: float,
        skill_gaps: list[str],
    ) -> float:
        return similarity_score