"""
End-to-end API test with a real MongoDB, the real embedding model and a real
FAISS index (in a temporary directory).

Resumes are ingested through ResumeService with already-extracted data, so
the PDF parsing and the local LLM are not exercised here; everything after
extraction (candidate building, embedding, indexing, storage, job creation,
matching, ranking and the HTTP layer) is real.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_candidate_search_service,
    get_job_service,
    get_recommendation_service,
)
from app.core.config.settings import settings
from app.core.constants.app_constants import EMBEDDING_VERSION
from app.database.vector_db.faiss_manager import FaissManager
from app.main import app
from app.services.resume_service import ResumeService


pytestmark = pytest.mark.integration


RESUMES = {
    "data-engineer": {
        "summary": "Data engineer building batch pipelines.",
        "skills": ["Python", "Spark", "SQL", "Docker"],
        "experience": [
            {
                "role": "Data Engineer",
                "company": "Acme",
                "start_date": "2019",
                "end_date": "2025",
                "description": ["Built Spark ETL pipelines in Python and SQL."],
            }
        ],
    },
    "frontend": {
        "summary": "Frontend developer.",
        "skills": ["JavaScript", "TypeScript", "React", "CSS"],
        "experience": [
            {
                "role": "Frontend Developer",
                "company": "Globex",
                "start_date": "2022",
                "end_date": "2025",
                "description": ["Built React interfaces."],
            }
        ],
    },
    "junior-data": {
        "summary": "Junior data engineer.",
        "skills": ["Python", "SQL"],
        "experience": [
            {
                "role": "Data Intern",
                "company": "Initech",
                "start_date": "2025",
                "end_date": "2025",
                "description": ["Wrote SQL reports."],
            }
        ],
    },
}

JOB_DESCRIPTION = """Data Engineer

We need a data engineer with at least 3 years of experience.

Requirements

Python
Spark
SQL
Docker

Responsibilities

Build and maintain data pipelines
"""


@pytest.fixture
def ingested(database, tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings, "FAISS_INDEX_PATH", str(tmp_path / "candidate.index")
    )
    monkeypatch.setattr(FaissManager, "_instance", None)

    service = ResumeService(resume_pipeline=None)

    for resume_id, extracted in RESUMES.items():
        candidate = service._build_candidate(resume_id, extracted)
        service._save_candidate(candidate)

    return service


def clear_service_caches():
    get_job_service.cache_clear()
    get_candidate_search_service.cache_clear()
    get_recommendation_service.cache_clear()


@pytest.fixture
def http(ingested):
    clear_service_caches()

    yield TestClient(app, raise_server_exceptions=False)

    clear_service_caches()


def create_job(http):
    response = http.post(
        "/api/v1/jobs/",
        json={"title": "Data Engineer", "description": JOB_DESCRIPTION},
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_health_with_real_database(http):
    response = http.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_ingestion_stores_candidates_and_vectors(database, ingested):
    documents = list(database["candidates"].find({}))

    assert len(documents) == len(RESUMES)
    assert {d["embedding_version"] for d in documents} == {EMBEDDING_VERSION}
    assert sorted(d["faiss_id"] for d in documents) == [1, 2, 3]
    assert ingested.vector_store.indexed_ids() == {1, 2, 3}


def test_create_job_persists_structured_fields(database, http):
    job = create_job(http)

    stored = database["jobs"].find_one({"title": "Data Engineer"})

    assert job["_id"] == str(stored["_id"])
    assert {"python", "spark", "sql", "docker"} <= set(stored["required_skills"])
    assert stored["experience_years"] == 3
    assert stored["responsibilities"] == ["Build and maintain data pipelines"]


def test_matching_ranks_the_data_engineer_first(http):
    job = create_job(http)

    response = http.get(f"/api/v1/matches/{job['_id']}")

    assert response.status_code == 200, response.text

    body = response.json()
    results = body["results"]

    assert body["metadata"]["scoring_mode"] == "hybrid"
    assert results, "expected at least one ranked candidate"
    assert results[0]["candidate_profile"]["resume_id"] == "data-engineer"

    top = results[0]

    assert top["score_breakdown"]["skill_score"] == 100.0
    assert top["score_breakdown"]["experience_score"] == 100.0
    assert top["skill_gaps"] == []

    scores = [item["similarity_score"] for item in results]

    assert scores == sorted(scores, reverse=True)

    frontend = [
        item
        for item in results
        if item["candidate_profile"]["resume_id"] == "frontend"
    ]

    assert not frontend or frontend[0]["similarity_score"] < top["similarity_score"]


def test_unknown_job_returns_404_with_real_database(http):
    response = http.get("/api/v1/matches/665f1c2b8e4a4b0012345678")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_malformed_job_id_returns_404_with_real_database(http):
    response = http.get("/api/v1/matches/not-an-object-id")

    assert response.status_code == 404


def test_legacy_candidate_with_string_description_does_not_break_matching(
    database, http
):
    """
    An older document (string experience description, no summary, no
    embedding version) must still be returned by a match instead of
    failing the whole request.
    """

    job = create_job(http)

    document = database["candidates"].find_one({"resume_id": "junior-data"})
    database["candidates"].update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "experience.0.description": "Wrote SQL reports.",
                "embedding_version": None,
            },
            "$unset": {"summary": ""},
        },
    )

    response = http.get(f"/api/v1/matches/{job['_id']}")

    assert response.status_code == 200, response.text


def test_semantic_search_finds_the_matching_candidate(http):
    response = http.post(
        "/api/v1/search/candidates",
        json={"query": "Data Engineer Python Spark SQL Docker", "top_k": 3},
    )

    assert response.status_code == 200, response.text

    results = response.json()["results"]

    assert results
    assert "python" in [s.lower() for s in results[0]["candidate"]["skills"]]
    assert all(0 <= hit["score"] <= 100 for hit in results)

    scores = [hit["score"] for hit in results]

    assert scores == sorted(scores, reverse=True)


def test_recommendations_name_the_skills_a_candidate_lacks(http, database):
    job = create_job(http)

    junior = database["candidates"].find_one({"resume_id": "junior-data"})

    response = http.get(
        "/api/v1/recommendations/",
        params={"job_id": job["_id"], "candidate_id": str(junior["_id"])},
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert {"spark", "docker"} <= set(body["missing_skills"])
    assert "python" not in body["missing_skills"]
    assert isinstance(body["recommendations"], list)


def test_resume_catalog_endpoints_on_ingested_data(http, database):
    # the ingested candidates were created without resume documents, so the
    # candidate list is the part that can be checked end to end here
    body = http.get("/api/v1/candidates/?skill=python").json()

    assert body["total"] == 2
