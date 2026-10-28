from types import SimpleNamespace

import numpy as np
import pytest

from app.evaluation.pooling import ProfileEmbedder
from app.matching.embedding_text import (
    SECTION_CHAR_BUDGET,
    CandidateTextBuilder,
    JobTextBuilder,
)
from app.models.candidate import CandidateModel, Experience, Project
from app.models.job import JobModel


def make_candidate(**overrides):
    values = {
        "resume_id": "r1",
        "faiss_id": 1,
        "summary": "Backend engineer who ships reliable services.",
        "skills": ["Python", "SQL"],
        "normalized_skills": ["python", "sql", "python"],
        "experience": [
            Experience(
                role="Backend Engineer",
                description=["Built payment APIs.", "Built payment APIs."],
                achievements=["Cut latency by 30%."],
            ),
            Experience(role="Backend Engineer", description=["Ran on-call."]),
            Experience(role="Intern", description=[]),
        ],
        "projects": [
            Project(title="Resume Miner", technologies=["fastapi", "faiss"]),
        ],
    }
    values.update(overrides)
    return CandidateModel(**values)


def test_candidate_sections_cover_profile():
    sections = CandidateTextBuilder().sections(make_candidate())

    assert list(sections) == ["headline", "skills", "experience", "projects"]
    assert sections["headline"].startswith("Backend Engineer, Intern.")
    assert "ships reliable services" in sections["headline"]
    assert sections["skills"] == "python, sql"
    assert sections["experience"] == (
        "Built payment APIs. Cut latency by 30%. Ran on-call."
    )
    assert sections["projects"] == "Resume Miner: fastapi, faiss"


def test_candidate_text_orders_sections_by_importance():
    text = CandidateTextBuilder().text(make_candidate())

    assert text.index("Backend Engineer") < text.index("python")
    assert text.index("python") < text.index("Built payment APIs")
    assert text.index("Built payment APIs") < text.index("Resume Miner")


def test_candidate_falls_back_to_raw_skills_and_skips_empty_sections():
    candidate = make_candidate(
        normalized_skills=[],
        summary=None,
        experience=[],
        projects=[],
    )

    assert CandidateTextBuilder().sections(candidate) == {
        "skills": "Python, SQL",
    }


def test_candidate_without_any_content_gives_empty_text():
    candidate = make_candidate(
        skills=[], normalized_skills=[], summary=None, experience=[], projects=[]
    )

    assert CandidateTextBuilder().text(candidate) == ""


def test_long_summary_cannot_push_skills_out_of_the_window():
    candidate = make_candidate(summary="x" * 5000)

    sections = CandidateTextBuilder().sections(candidate)

    assert len(sections["headline"]) <= SECTION_CHAR_BUDGET["headline"]
    assert sections["skills"] == "python, sql"


def test_job_sections_use_responsibilities_when_available():
    job = JobModel(
        title="Backend Engineer",
        description="Whole job description",
        required_skills=["python"],
        normalized_skills=["python", "sql"],
        responsibilities=["Build APIs", "Write tests"],
        occupation="Software Developers",
    )

    sections = JobTextBuilder().sections(job)

    assert sections == {
        "headline": "Backend Engineer. Software Developers",
        "skills": "python, sql",
        "responsibilities": "Build APIs Write tests",
    }


def test_job_falls_back_to_description_without_responsibilities():
    job = JobModel(
        title="Dev",
        description="Build things",
        required_skills=["python"],
    )

    sections = JobTextBuilder().sections(job)

    assert sections["responsibilities"] == "Build things"
    assert sections["skills"] == "python"


def test_builders_accept_plain_objects():
    candidate = SimpleNamespace(skills=["go"], experience=None, projects=None)

    assert CandidateTextBuilder().text(candidate) == "go"


# ------------------------------------------------------ evaluation pooling


class FixedEncoder:
    def __init__(self):
        self.calls = 0

    def encode(self, texts):
        self.calls += 1

        vectors = np.zeros((len(texts), 2), dtype=np.float32)

        for row, text in enumerate(texts):
            if text == "":
                vectors[row] = [0.0, 1.0]
            elif text.startswith("a"):
                vectors[row] = [1.0, 0.0]
            else:
                vectors[row] = [0.0, 1.0]

        return vectors


def test_profile_embedder_pools_sections_with_weights():
    embedder = ProfileEmbedder(FixedEncoder(), weights={"x": 3.0, "y": 1.0})

    vector = embedder.embed({"x": "a section", "y": "b section"})

    expected = np.array([3.0, 1.0]) / np.linalg.norm([3.0, 1.0])

    assert np.allclose(vector, expected)


def test_profile_embedder_batches_into_one_encoder_call():
    encoder = FixedEncoder()

    matrix = ProfileEmbedder(encoder).embed_many(
        [{"skills": "a1", "headline": "b1"}, {"skills": "a2"}]
    )

    assert encoder.calls == 1
    assert matrix.shape == (2, 2)
    assert np.allclose(np.linalg.norm(matrix, axis=1), 1.0)


def test_profile_embedder_falls_back_for_empty_profile():
    vector = ProfileEmbedder(FixedEncoder()).embed({"skills": "   "})

    assert np.allclose(vector, [0.0, 1.0])
