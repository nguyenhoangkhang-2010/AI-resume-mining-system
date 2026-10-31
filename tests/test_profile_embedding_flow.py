import numpy as np
import pytest
from bson import ObjectId
from loguru import logger
from pydantic import ValidationError
from types import SimpleNamespace

from app.core.constants.app_constants import EMBEDDING_VERSION
from app.matching.embedding_text import CandidateTextBuilder, JobTextBuilder
from app.matching.ranking.candidate_scorer import HybridCandidateScorer
from app.matching.ranking.ranking_pipeline import RankingPipeline
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.services.matching_service import MatchingService
from app.services.resume_service import ResumeService


class RecordingEmbeddingService:
    def __init__(self):
        self.texts = []

    def generate_embedding(self, text):
        self.texts.append(text)
        return np.array([1.0, 0.0], dtype=np.float32)


class RecordingVectorStore:
    def __init__(self):
        self.added = []

    def add_candidate_embedding(self, faiss_id, embedding):
        self.added.append(faiss_id)
        return True


class LowercaseNormalizer:
    def normalize(self, skill):
        return skill.lower()


def make_resume_service():
    service = ResumeService.__new__(ResumeService)
    service.embedding_service = RecordingEmbeddingService()
    service.vector_store = RecordingVectorStore()
    service.skill_normalizer = LowercaseNormalizer()
    service.candidate_text_builder = CandidateTextBuilder()
    service._generate_faiss_id = lambda: 7

    return service


EXTRACTED = {
    "summary": "Data engineer focused on pipelines.",
    "skills": ["Python", "Spark"],
    "experience": [
        {"role": "Data Engineer", "company": "Acme", "description": ["Built ETL jobs."]}
    ],
    "projects": [{"title": "Lakehouse", "technologies": ["spark"]}],
}


def test_candidate_embedding_uses_profile_text_not_just_skills():
    service = make_resume_service()

    candidate = service._build_candidate("resume-1", EXTRACTED)

    text = service.embedding_service.texts[0]

    assert "Data Engineer" in text
    assert "pipelines" in text
    assert "python, spark" in text
    assert "Built ETL jobs." in text
    assert "Lakehouse" in text
    assert service.vector_store.added == [candidate.faiss_id]


def test_candidate_keeps_summary_and_embedding_version():
    candidate = make_resume_service()._build_candidate("resume-1", EXTRACTED)

    assert candidate.summary == "Data engineer focused on pipelines."
    assert candidate.embedding_version == EMBEDDING_VERSION


def test_non_string_summary_is_ignored():
    candidate = make_resume_service()._build_candidate(
        "resume-1", {**EXTRACTED, "summary": {"unexpected": 1}}
    )

    assert candidate.summary is None


def test_invalid_data_does_not_leave_a_vector_behind():
    service = make_resume_service()

    with pytest.raises(ValidationError):
        service._build_candidate(
            "resume-1",
            {**EXTRACTED, "experience": [{"role": {"not": "a string"}}]},
        )

    assert service.vector_store.added == []
    assert service.embedding_service.texts == []


# ------------------------------------------------------------ matching side


class SearchStore:
    def search_similar_candidates(self, embedding, top_k):
        return [{"faiss_id": 1, "similarity_score": 0.9}]


class Collection:
    def __init__(self, documents):
        self.documents = documents

    def find_one(self, query):
        return self.documents[0]

    def find(self, query):
        return self.documents


def make_matching_service(monkeypatch, candidate_version):
    job = JobModel(
        title="Data Engineer",
        description="d",
        required_skills=["python"],
        normalized_skills=["python"],
        responsibilities=["Build pipelines"],
    )
    candidate = CandidateModel(
        resume_id="r1",
        faiss_id=1,
        skills=["python"],
        normalized_skills=["python"],
        embedding_version=candidate_version,
    )

    embeddings = RecordingEmbeddingService()

    service = MatchingService.__new__(MatchingService)
    service.embedding_service = embeddings
    service.vector_store = SearchStore()
    service.job_text_builder = JobTextBuilder()
    service.ranking_config = SimpleNamespace(retrieval_top_k=50)
    service.ranking_pipeline = RankingPipeline(
        candidate_scorer=HybridCandidateScorer()
    )

    job_document = {"_id": ObjectId(), **job.model_dump(by_alias=True, exclude={"id"})}
    candidate_document = {
        "_id": ObjectId(),
        **candidate.model_dump(by_alias=True, exclude={"id"}),
    }

    monkeypatch.setattr(
        MatchingService, "jobs_col", property(lambda self: Collection([job_document]))
    )
    monkeypatch.setattr(
        MatchingService,
        "candidates_col",
        property(lambda self: Collection([candidate_document])),
    )

    return service, embeddings, str(job_document["_id"])


def capture_warnings():
    captured = []
    sink_id = logger.add(captured.append, level="WARNING", format="{message}")

    return captured, sink_id


def test_job_embedding_uses_title_skills_and_responsibilities(monkeypatch):
    service, embeddings, job_id = make_matching_service(
        monkeypatch, EMBEDDING_VERSION
    )

    service.match_candidates_for_job(job_id)

    assert embeddings.texts == ["Data Engineer python Build pipelines"]


def test_stale_candidate_vectors_are_reported(monkeypatch):
    service, _, job_id = make_matching_service(monkeypatch, "skills-v0")

    captured, sink_id = capture_warnings()

    try:
        service.match_candidates_for_job(job_id)
    finally:
        logger.remove(sink_id)

    assert any("reindex_candidates.py" in str(message) for message in captured)


def test_current_candidate_vectors_do_not_warn(monkeypatch):
    service, _, job_id = make_matching_service(monkeypatch, EMBEDDING_VERSION)

    captured, sink_id = capture_warnings()

    try:
        service.match_candidates_for_job(job_id)
    finally:
        logger.remove(sink_id)

    assert not any("reindex" in str(message) for message in captured)
