"""
The list, detail and delete endpoints against a real MongoDB, so sorting,
paging, counts, the case-insensitive collation and the delete cascade are
checked with the real query engine and not only with the in-memory fake.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_candidate_service,
    get_job_service,
    get_resume_catalog_service,
)
from app.main import app
from app.models.candidate import CandidateModel
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.services.resume_catalog_service import ResumeCatalogService

pytestmark = pytest.mark.integration

BASE = datetime(2026, 1, 1)


class RecordingVectorStore:
    def __init__(self):
        self.removed = []

    def remove_candidate_embedding(self, faiss_id):
        self.removed.append(faiss_id)
        return True


@pytest.fixture
def http(database, tmp_path):
    store = RecordingVectorStore()

    app.dependency_overrides[get_resume_catalog_service] = lambda: ResumeCatalogService(
        store, tmp_path
    )
    app.dependency_overrides[get_candidate_service] = CandidateService
    app.dependency_overrides[get_job_service] = lambda: JobService.__new__(JobService)

    yield TestClient(app, raise_server_exceptions=False), store, database, tmp_path

    app.dependency_overrides.clear()


def resume(index, status="processed", **extra):
    return {
        "filename": f"cv-{index}.pdf",
        "file_path": "ignored",
        "upload_status": status,
        "created_at": BASE + timedelta(minutes=index),
        **extra,
    }


def candidate(index, resume_id, skills):
    model = CandidateModel(
        resume_id=resume_id,
        faiss_id=100 + index,
        skills=skills,
        normalized_skills=skills,
        personal_info={"full_name": f"Person {index}", "email": f"p{index}@example.com"},
    )

    document = model.model_dump(by_alias=True, exclude={"id"})
    document["created_at"] = BASE + timedelta(minutes=index)

    return document


def test_resumes_are_listed_newest_first_with_exact_counts(http):
    client, _, database, _ = http

    database["resumes"].insert_many([resume(i) for i in range(7)])

    first = client.get("/api/v1/resumes/?limit=3").json()
    last = client.get("/api/v1/resumes/?limit=3&offset=6").json()

    assert first["total"] == 7
    assert [i["filename"] for i in first["items"]] == ["cv-6.pdf", "cv-5.pdf", "cv-4.pdf"]
    assert [i["filename"] for i in last["items"]] == ["cv-0.pdf"]


def test_status_filter_counts_only_matching_resumes(http):
    client, _, database, _ = http

    database["resumes"].insert_many(
        [resume(1), resume(2, "failed", status_reason="unreadable_file"), resume(3, "failed")]
    )

    body = client.get("/api/v1/resumes/?status=failed").json()

    assert body["total"] == 2
    assert {i["status"] for i in body["items"]} == {"failed"}


def test_resume_detail_finds_its_candidate(http):
    client, _, database, _ = http

    resume_id = database["resumes"].insert_one(resume(1)).inserted_id
    candidate_id = database["candidates"].insert_one(
        candidate(1, str(resume_id), ["python"])
    ).inserted_id

    body = client.get(f"/api/v1/resumes/{resume_id}").json()

    assert body["candidate_id"] == str(candidate_id)


def test_delete_cascades_to_candidate_vector_and_file(http):
    client, store, database, upload_dir = http

    file = upload_dir / "cv.pdf"
    file.write_bytes(b"%PDF-1.7")

    resume_id = database["resumes"].insert_one(resume(1, file_path=str(file))).inserted_id
    database["candidates"].insert_one(candidate(1, str(resume_id), ["python"]))
    database["candidates"].insert_one(candidate(2, "other", ["java"]))

    assert client.delete(f"/api/v1/resumes/{resume_id}").status_code == 204

    assert database["resumes"].count_documents({}) == 0
    assert database["candidates"].count_documents({}) == 1
    assert store.removed == [101]
    assert not file.exists()


def test_skill_filter_is_case_insensitive_with_real_collation(http):
    client, _, database, _ = http

    database["candidates"].insert_many(
        [
            candidate(1, "a", ["Python", "SQL"]),
            candidate(2, "b", ["java"]),
            candidate(3, "c", ["python"]),
        ]
    )

    body = client.get("/api/v1/candidates/?skill=PYTHON").json()

    assert body["total"] == 2
    assert {i["full_name"] for i in body["items"]} == {"Person 1", "Person 3"}


def test_candidate_detail_round_trips_through_mongo(http):
    client, _, database, _ = http

    candidate_id = database["candidates"].insert_one(
        candidate(1, "a", ["python"])
    ).inserted_id

    body = client.get(f"/api/v1/candidates/{candidate_id}").json()

    assert body["id"] == str(candidate_id)
    assert body["personal_info"]["email"] == "p1@example.com"


def test_jobs_list_get_and_delete(http):
    client, _, database, _ = http

    ids = [
        database["jobs"].insert_one(
            {
                "title": f"Job {i}",
                "description": "d",
                "raw_text": "d",
                "required_skills": ["python"],
                "created_at": BASE + timedelta(minutes=i),
                "updated_at": BASE,
            }
        ).inserted_id
        for i in range(3)
    ]

    listing = client.get("/api/v1/jobs/?limit=2").json()

    assert listing["total"] == 3
    assert [j["title"] for j in listing["items"]] == ["Job 2", "Job 1"]

    assert client.get(f"/api/v1/jobs/{ids[0]}").json()["title"] == "Job 0"
    assert client.delete(f"/api/v1/jobs/{ids[0]}").status_code == 204
    assert database["jobs"].count_documents({}) == 2
    assert client.get(f"/api/v1/jobs/{ids[0]}").status_code == 404
