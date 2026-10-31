from types import SimpleNamespace

import pytest

from app.extraction.job.experience_years_extractor import (
    ExperienceYearsExtractor,
)
from app.job_processing.pipelines.job_pipeline import JobPipeline
from app.schemas.job_schema import JobCreateRequest
from app.services.job_service import JobService
from app.services.matching_service import MatchingService


class FakePipeline:
    def __init__(self, result):
        self.result = result
        self.received = None

    def process(self, source):
        self.received = source
        return self.result


class FakeNormalizer:
    def normalize(self, skill):
        return skill.lower().strip()


class FakeOccupationMatcher:
    def __init__(self, occupations=None):
        self.occupations = occupations or {}

    def find(self, text):
        return self.occupations.get(text.casefold().strip())


class FakeCollection:
    def __init__(self, document=None):
        self.inserted = []
        self.document = document

    def insert_one(self, document):
        self.inserted.append(document)
        return SimpleNamespace(inserted_id="665f1c2b8e4a4b0012345678")

    def find_one(self, query):
        return self.document


@pytest.fixture
def collection(monkeypatch):
    fake = FakeCollection()
    monkeypatch.setattr(
        JobService,
        "jobs_col",
        property(lambda self: fake),
    )
    return fake


def build_service(pipeline_result, occupations=None):
    return JobService(
        job_pipeline=FakePipeline(pipeline_result),
        skill_normalizer=FakeNormalizer(),
        occupation_matcher=FakeOccupationMatcher(occupations),
    )


def test_create_job_populates_structured_fields(collection):
    service = build_service(
        {
            "requirements": "Python\nDocker",
            "responsibilities": "- Develop APIs\n2) Write tests\n\n",
            "skills": ["python", "docker", "python"],
        },
        occupations={
            "software engineer": {"name": "Software Developers"},
        },
    )

    response = service.create_job(
        JobCreateRequest(
            title="Software Engineer",
            description="Need 3+ years of experience.\nPython, Docker",
        )
    )

    assert response.id == "665f1c2b8e4a4b0012345678"
    assert response.required_skills == ["python", "docker"]
    assert response.normalized_skills == ["python", "docker"]
    assert response.responsibilities == ["Develop APIs", "Write tests"]
    assert response.experience_years == 3
    assert response.occupation == "Software Developers"
    assert response.raw_text == (
        "Need 3+ years of experience.\nPython, Docker"
    )


def test_create_job_persists_all_fields(collection):
    service = build_service(
        {"requirements": None, "responsibilities": None, "skills": ["Python"]}
    )

    service.create_job(
        JobCreateRequest(title="Dev", description="Python developer")
    )

    saved = collection.inserted[0]

    assert "_id" not in saved
    assert saved["required_skills"] == ["Python"]
    assert saved["normalized_skills"] == ["python"]
    assert saved["raw_text"] == "Python developer"
    assert saved["occupation"] is None


def test_create_job_with_no_extracted_data(collection):
    service = build_service(
        {"requirements": None, "responsibilities": None, "skills": []}
    )

    response = service.create_job(
        JobCreateRequest(title="Dev", description="Something vague")
    )

    assert response.required_skills == []
    assert response.responsibilities == []
    assert response.experience_years is None


def test_create_job_with_real_pipeline(collection):
    service = JobService(
        job_pipeline=JobPipeline(),
        skill_normalizer=FakeNormalizer(),
        occupation_matcher=FakeOccupationMatcher(),
    )

    response = service.create_job(
        JobCreateRequest(
            title="Backend Engineer",
            description=(
                "Backend Engineer\n\n"
                "Requirements\n\nPython\nFastAPI\nDocker\n\n"
                "Responsibilities\n\nDevelop APIs\nWrite tests\n"
            ),
        )
    )

    assert "python" in response.required_skills
    assert "Develop APIs" in response.responsibilities


def test_job_create_request_rejects_empty_fields():
    with pytest.raises(ValueError):
        JobCreateRequest(title="", description="text")

    with pytest.raises(ValueError):
        JobCreateRequest(title="Dev", description="")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3+ years of experience", 3),
        ("2-4 years experience", 2),
        ("minimum 5 yrs in Python, 2 years of Docker", 5),
        ("Five years of experience", None),
        ("candidates must be 18 years old", None),
        ("", None),
    ],
)
def test_experience_years_extractor(text, expected):
    assert ExperienceYearsExtractor.extract(text) == expected


def test_matching_service_invalid_job_id_returns_none(monkeypatch):
    service = MatchingService.__new__(MatchingService)

    monkeypatch.setattr(
        MatchingService,
        "jobs_col",
        property(lambda self: FakeCollection()),
    )

    assert service._get_job("not-an-object-id") is None
    assert service._get_job(None) is None


def test_matching_service_loads_job_with_new_fields(monkeypatch):
    document = {
        "_id": __import__("bson").ObjectId(),
        "title": "Dev",
        "description": "d",
        "raw_text": "d",
        "required_skills": ["python"],
        "normalized_skills": ["python"],
        "experience_years": 2,
        "responsibilities": ["build"],
        "occupation": None,
        "faiss_id": None,
    }

    service = MatchingService.__new__(MatchingService)

    monkeypatch.setattr(
        MatchingService,
        "jobs_col",
        property(lambda self: FakeCollection(document)),
    )

    job = service._get_job(str(document["_id"]))

    assert job.required_skills == ["python"]
    assert job.experience_years == 2
