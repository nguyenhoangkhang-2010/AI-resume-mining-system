import re

from loguru import logger

from app.database.mongodb.connection import mongo_db
from app.extraction.job.experience_years_extractor import (
    ExperienceYearsExtractor,
)
from app.extraction.occupations.matcher import OccupationMatcher
from app.job_processing.pipelines.job_pipeline import JobPipeline
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)
from app.models.job import JobModel
from app.core.exceptions import NotFoundError
from app.core.identifiers import parse_object_id
from app.schemas.job_schema import JobCreateRequest, JobResponse, JobSummary
from app.schemas.page import Page


BULLET_PREFIX = re.compile(r"^\s*(?:[-•*·–]|\d+[.)])\s*")


class JobService:
    def __init__(
        self,
        job_pipeline: JobPipeline | None = None,
        skill_normalizer=None,
        occupation_matcher: OccupationMatcher | None = None,
    ):
        self.job_pipeline = job_pipeline or JobPipeline()
        self.skill_normalizer = skill_normalizer or create_skill_normalizer()
        self.occupation_matcher = occupation_matcher or OccupationMatcher()

    @property
    def db(self):
        return mongo_db.get_db()

    @property
    def jobs_col(self):
        return self.db["jobs"]

    def create_job(self, request: JobCreateRequest) -> JobResponse:
        logger.info(f"Creating job: '{request.title}'")

        description = request.description.strip()

        job_data = self.job_pipeline.process(description)

        required_skills = self._unique(job_data.get("skills") or [])

        normalized_skills = self._unique(
            self.skill_normalizer.normalize(skill)
            for skill in required_skills
        )

        job_model = JobModel(
            title=request.title,
            description=description,
            raw_text=request.description,
            required_skills=required_skills,
            normalized_skills=normalized_skills,
            experience_years=ExperienceYearsExtractor.extract(description),
            responsibilities=self._split_lines(
                job_data.get("responsibilities")
            ),
            occupation=self._find_occupation(request.title),
        )

        job_id = self._save_job(job_model)
        job_model.id = job_id

        logger.success(f"Successfully created job (ID: {job_id})")
        return JobResponse.model_validate(job_model)

    def list_jobs(self, limit: int, offset: int) -> Page[JobSummary]:
        documents = (
            self.jobs_col.find({})
            .sort([("created_at", -1), ("_id", -1)])
            .skip(offset)
            .limit(limit)
        )

        return Page[JobSummary](
            items=[
                JobSummary(
                    id=str(document["_id"]),
                    title=document.get("title", ""),
                    occupation=document.get("occupation"),
                    required_skills=document.get("required_skills") or [],
                    experience_years=document.get("experience_years"),
                    created_at=document["created_at"],
                )
                for document in documents
            ],
            total=self.jobs_col.count_documents({}),
            limit=limit,
            offset=offset,
        )

    def get_job_response(self, job_id: str) -> JobResponse:
        document = self.jobs_col.find_one({"_id": parse_object_id(job_id, "Job")})

        if not document:
            raise NotFoundError(f"Job not found: {job_id}")

        document["_id"] = str(document["_id"])

        return JobResponse.model_validate(JobModel(**document))

    def delete_job(self, job_id: str) -> None:
        result = self.jobs_col.delete_one({"_id": parse_object_id(job_id, "Job")})

        if result.deleted_count == 0:
            raise NotFoundError(f"Job not found: {job_id}")

    def _find_occupation(self, title: str) -> str | None:
        occupation = self.occupation_matcher.find(title)

        if not occupation:
            return None

        return occupation.get("name")

    def _save_job(self, job: JobModel) -> str:
        result = self.jobs_col.insert_one(job.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    @staticmethod
    def _unique(values) -> list[str]:
        seen = set()
        result = []

        for value in values:
            if not isinstance(value, str) or not value.strip():
                continue

            if value in seen:
                continue

            seen.add(value)
            result.append(value)

        return result

    @staticmethod
    def _split_lines(text: str | None) -> list[str]:
        if not text:
            return []

        lines = (BULLET_PREFIX.sub("", line).strip() for line in text.splitlines())

        return [line for line in lines if line]
