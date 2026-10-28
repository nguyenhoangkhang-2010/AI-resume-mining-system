from types import SimpleNamespace

import pytest
from bson import ObjectId

from app.matching.confidence.confidence_calculator import (
    ConfidenceCalculator,
)
from app.matching.explanation.explanation_engine import ExplanationEngine
from app.matching.ranking.candidate_scorer import HybridCandidateScorer
from app.matching.ranking.ranking_pipeline import RankingPipeline
from app.matching.scoring.experience_scorer import (
    ExperienceCalculator,
    ExperienceScorer,
)
from app.matching.scoring.skill_overlap_scorer import SkillOverlapScorer
from app.matching.scoring.weighted_scorer import WeightedScorer
from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)
from app.models.candidate import CandidateModel, Experience
from app.models.job import JobModel
from app.services.matching_service import MatchingService


def make_job(**overrides):
    values = {
        "title": "Backend Engineer",
        "description": "Backend role",
        "required_skills": ["python", "sql", "docker"],
        "normalized_skills": ["python", "sql", "docker"],
        "experience_years": None,
    }
    values.update(overrides)
    return JobModel(**values)


def make_candidate(faiss_id, skills, experience=None, **overrides):
    values = {
        "resume_id": f"resume-{faiss_id}",
        "skills": skills,
        "normalized_skills": [skill.lower() for skill in skills],
        "experience": experience or [],
        "faiss_id": faiss_id,
    }
    values.update(overrides)
    return CandidateModel(**values)


# ---------------------------------------------------------------- weighted scorer


def test_weighted_score_without_experience_keeps_original_weights():
    assert WeightedScorer().calculate(90, 80) == 86.0


def test_weighted_score_with_experience_uses_fixed_share():
    # 0.8 * (0.6 * 90 + 0.4 * 80) + 0.2 * 100
    assert WeightedScorer().calculate(90, 80, 100) == 88.8


def test_weighted_score_without_skills_uses_semantic_only():
    assert WeightedScorer().calculate(None, 80) == 80.0


def test_weighted_score_without_skills_but_with_experience():
    assert WeightedScorer().calculate(None, 80, 50) == 74.0


def test_weighted_score_with_nothing_is_zero():
    assert WeightedScorer().calculate(None, None) == 0.0


# ---------------------------------------------------------------- confidence / explanation


def test_confidence_uses_available_components_only():
    assert ConfidenceCalculator.calculate(90, 80) == 85.0
    assert ConfidenceCalculator.calculate(None, 80) == 80.0
    assert ConfidenceCalculator.calculate(90, 80, 100) == 90.0
    assert ConfidenceCalculator.calculate(None, None) == 0.0


def test_explanation_lists_matched_and_missing_skills():
    explanation = ExplanationEngine.generate(
        skill_score=50,
        semantic_score=80,
        overall_score=62,
        experience_score=100,
        matched_skills=["python"],
        missing_skills=["sql"],
    )

    assert "Matched skills: python" in explanation["matched_skills"]
    assert "Missing skills: sql" in explanation["missing_skills"]
    assert "experience_score" in explanation


def test_hybrid_strategy_returns_components():
    result = HybridMatchingStrategy().match(
        candidate_id="c1",
        job_id="j1",
        skill_score=50,
        semantic_score=80,
        experience_score=100,
        matched_skills=["python"],
        missing_skills=["sql"],
    )

    assert result.overall_score == 69.6
    assert result.experience_score == 100
    assert result.matched_skills == ["python"]
    assert result.missing_skills == ["sql"]


# ---------------------------------------------------------------- skill overlap


def test_skill_overlap_scores_coverage():
    overlap = SkillOverlapScorer().score(
        ["python", "sql", "docker", "git"],
        ["Python", "  Docker "],
    )

    assert overlap.score == 50.0
    assert overlap.matched == ["python", "docker"]
    assert overlap.missing == ["sql", "git"]


def test_skill_overlap_ignores_duplicates_and_blanks():
    overlap = SkillOverlapScorer().score(
        ["python", "Python", "", "sql"],
        ["python"],
    )

    assert overlap.score == 50.0


def test_skill_overlap_without_requirements_has_no_score():
    overlap = SkillOverlapScorer().score([], ["python"])

    assert overlap.score is None
    assert overlap.missing == []


# ---------------------------------------------------------------- experience


def test_experience_calculator_merges_overlapping_jobs():
    experiences = [
        {"start_date": "2018", "end_date": "2020"},
        {"start_date": "2019", "end_date": "2022"},
        {"start_date": "2024", "end_date": "2025"},
    ]

    years = ExperienceCalculator().total_years(
        experiences,
        current_year=2026,
    )

    assert years == 5.0


def test_experience_calculator_handles_present_and_models():
    experiences = [
        Experience(start_date="Jan 2023", end_date="Present"),
    ]

    years = ExperienceCalculator().total_years(
        experiences,
        current_year=2026,
    )

    assert years == 3.0


def test_experience_calculator_is_conservative_without_end_date():
    years = ExperienceCalculator().total_years(
        [{"start_date": "2021", "end_date": None}],
        current_year=2026,
    )

    assert years == 0.0


def test_experience_calculator_ignores_unparseable_and_future_dates():
    years = ExperienceCalculator().total_years(
        [
            {"start_date": "unknown", "end_date": "unknown"},
            {"start_date": "2040", "end_date": "2042"},
            {"start_date": "2022", "end_date": "2019"},
        ],
        current_year=2026,
    )

    assert years == 0.0


@pytest.mark.parametrize(
    "required, candidate_years, expected",
    [
        (None, 5, None),
        (0, 5, None),
        (4, 2, 50.0),
        (4, 10, 100.0),
        (3, 0, 0.0),
    ],
)
def test_experience_scorer(required, candidate_years, expected):
    assert ExperienceScorer().score(required, candidate_years) == expected


# ---------------------------------------------------------------- candidate scorer


def test_candidate_scorer_combines_all_components():
    job = make_job(experience_years=2)
    candidate = make_candidate(
        1,
        ["Python", "SQL"],
        experience=[
            Experience(start_date="2020", end_date="2024"),
        ],
    )

    score = HybridCandidateScorer().score(
        job=job,
        candidate=candidate,
        semantic_score=80,
    )

    assert score.skill_score == pytest.approx(66.67)
    assert score.experience_score == 100.0
    assert score.matched_skills == ["python", "sql"]
    assert score.missing_skills == ["docker"]
    assert score.overall_score == pytest.approx(
        0.8 * (0.6 * 66.67 + 0.4 * 80) + 0.2 * 100,
        abs=0.01,
    )


def test_candidate_scorer_job_without_skills_uses_semantic_only():
    job = make_job(required_skills=[], normalized_skills=[])
    candidate = make_candidate(1, ["Python"])

    score = HybridCandidateScorer().score(
        job=job,
        candidate=candidate,
        semantic_score=72,
    )

    assert score.skill_score is None
    assert score.overall_score == 72.0


def test_candidate_scorer_falls_back_to_raw_skills():
    job = make_job(normalized_skills=[])
    candidate = make_candidate(
        1,
        ["Python", "SQL", "Docker"],
        normalized_skills=[],
    )

    score = HybridCandidateScorer().score(
        job=job,
        candidate=candidate,
        semantic_score=50,
    )

    assert score.skill_score == 100.0


# ---------------------------------------------------------------- pipeline


def hybrid_pipeline():
    return RankingPipeline(candidate_scorer=HybridCandidateScorer())


def test_pipeline_ranks_skill_match_above_pure_semantic_match():
    job = make_job()

    skilled = make_candidate(1, ["Python", "SQL", "Docker"])
    unskilled = make_candidate(2, ["Photoshop"])

    result = hybrid_pipeline().process(
        job=job,
        candidates=[unskilled, skilled],
        score_map={1: 0.55, 2: 0.9},
    )

    assert result.results[0].candidate_profile.resume_id == "resume-1"


def test_pipeline_keeps_low_cosine_candidate_with_strong_skills():
    # Previously dropped by the 0.65 cosine pre-filter.
    result = hybrid_pipeline().process(
        job=make_job(),
        candidates=[make_candidate(1, ["Python", "SQL", "Docker"])],
        score_map={1: 0.5},
    )

    assert len(result.results) == 1
    assert result.results[0].similarity_score == pytest.approx(80.0)


def test_pipeline_filters_candidates_below_minimum_score():
    result = hybrid_pipeline().process(
        job=make_job(),
        candidates=[make_candidate(1, ["Photoshop"])],
        score_map={1: 0.4},
    )

    assert result.results == []
    assert result.metadata.filtered_candidates == 1
    assert result.metadata.scoring_mode == "hybrid"
    assert result.metadata.similarity_threshold == 50.0


def test_pipeline_exposes_breakdown_and_gaps():
    result = hybrid_pipeline().process(
        job=make_job(),
        candidates=[make_candidate(1, ["Python", "SQL"])],
        score_map={1: 0.8},
    )

    ranked = result.results[0]

    assert ranked.skill_gaps == ["docker"]
    assert ranked.score_breakdown.matched_skills == ["python", "sql"]
    assert ranked.score_breakdown.skill_score == pytest.approx(66.67)
    assert ranked.score_breakdown.semantic_score == 80.0
    assert "overall_score" in ranked.score_breakdown.explanation


def test_pipeline_without_candidate_scorer_keeps_similarity_mode():
    result = RankingPipeline().process(
        job=make_job(),
        candidates=[make_candidate(1, ["Python"])],
        score_map={1: 0.8},
    )

    assert result.metadata.scoring_mode == "similarity"
    assert result.results[0].score_breakdown is None


# ---------------------------------------------------------------- service


class FakeEmbeddingService:
    def generate_embedding(self, text):
        return [0.1, 0.2]


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.top_k = None

    def search_similar_candidates(self, embedding, top_k):
        self.top_k = top_k
        return self.results


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    def find_one(self, query):
        return self.documents[0]

    def find(self, query):
        wanted = set(query["faiss_id"]["$in"])
        return [d for d in self.documents if d["faiss_id"] in wanted]


def test_matching_service_returns_hybrid_ranking(monkeypatch):
    job_doc = {
        "_id": ObjectId(),
        **make_job().model_dump(by_alias=True, exclude={"id"}),
    }
    candidate_docs = [
        {
            "_id": ObjectId(),
            **make_candidate(
                faiss_id, skills
            ).model_dump(by_alias=True, exclude={"id"}),
        }
        for faiss_id, skills in [
            (1, ["Photoshop"]),
            (2, ["Python", "SQL", "Docker"]),
        ]
    ]

    vector_store = FakeVectorStore(
        [
            {"faiss_id": 1, "similarity_score": 0.9},
            {"faiss_id": 2, "similarity_score": 0.6},
        ]
    )

    service = MatchingService.__new__(MatchingService)
    service.embedding_service = FakeEmbeddingService()
    service.vector_store = vector_store
    service.ranking_pipeline = hybrid_pipeline()
    service.ranking_config = SimpleNamespace(retrieval_top_k=50)

    monkeypatch.setattr(
        MatchingService,
        "jobs_col",
        property(lambda self: FakeCollection([job_doc])),
    )
    monkeypatch.setattr(
        MatchingService,
        "candidates_col",
        property(lambda self: FakeCollection(candidate_docs)),
    )

    response = service.match_candidates_for_job(str(job_doc["_id"]))

    assert vector_store.top_k == 50
    assert response.metadata.scoring_mode == "hybrid"
    assert response.results[0].candidate_profile.resume_id == "resume-2"
    assert response.results[0].score_breakdown.skill_score == 100.0
