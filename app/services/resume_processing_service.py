from __future__ import annotations

from bson import ObjectId
from loguru import logger

from app.database.mongodb.connection import mongo_db
from app.models.candidate import (
    CandidateModel,
    Certification,
    Education,
    Experience,
    Project,
)
from app.models.resume import ResumeModel
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.embeddings.services.embedding_service import EmbeddingService
from app.vector_store.vector_store import VectorStore
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)


class ResumeProcessingService:

    def __init__(
        self,
        resume_pipeline: ResumePipeline,
    ) -> None:
        self.resume_pipeline = resume_pipeline
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.skill_normalizer = create_skill_normalizer()

    @property
    def db(self):
        return mongo_db.get_db()

    @property
    def resumes_col(self):
        return self.db["resumes"]

    @property
    def candidates_col(self):
        return self.db["candidates"]

    def process_pending_resume(
        self,
        resume_id: str,
    ) -> None:

        logger.info(
            "Starting background processing for resume: {}",
            resume_id,
        )

        self._update_resume_status(
            resume_id=resume_id,
            status="processing",
        )

        try:
            resume = self.resumes_col.find_one(
                {
                    "_id": ObjectId(resume_id),
                }
            )

            if not resume:
                raise ValueError(
                    f"Resume not found: {resume_id}"
                )

            file_path = resume.get("file_path")
            filename = resume.get("filename")

            if not file_path:
                raise ValueError(
                    f"Resume {resume_id} has no file path."
                )

            logger.info(
                "Processing resume '{}' from '{}'",
                filename,
                file_path,
            )

            extracted_data = (
                self.resume_pipeline.process_pdf(
                    file_path
                )
            )

            candidate = self._build_candidate(
                resume_id=resume_id,
                extracted_data=extracted_data,
            )

            self._insert_candidate(
                candidate
            )

            self._update_resume_status(
                resume_id=resume_id,
                status="processed",
                data=extracted_data,
            )

            logger.success(
                "Resume '{}' processed successfully.",
                filename,
            )

        except Exception as exc:

            logger.exception(
                "Background processing failed for resume {}: {}",
                resume_id,
                exc,
            )

            self._update_resume_status(
                resume_id=resume_id,
                status="failed",
            )

            raise

    def _build_candidate(
        self,
        resume_id: str,
        extracted_data: dict,
    ) -> CandidateModel:

        skills = (
            extracted_data.get("skills")
            or []
        )

        normalized_skills = [
            self.skill_normalizer.normalize(
                skill
            )
            for skill in skills
            if isinstance(skill, str)
            and skill.strip()
        ]

        embedding_text = " ".join(
            normalized_skills
        )

        embedding = (
            self.embedding_service.generate_embedding(
                embedding_text
            )
        )

        faiss_id = self._generate_faiss_id()

        self.vector_store.add_candidate_embedding(
            faiss_id=faiss_id,
            embedding=embedding,
        )

        education_models = [
            Education.model_validate(
                education
            )
            for education in (
                extracted_data.get("education")
                or []
            )
        ]

        experience_models = [
            Experience.model_validate(
                experience
            )
            for experience in (
                extracted_data.get("experience")
                or []
            )
        ]

        project_models = [
            Project.model_validate(
                project
            )
            for project in (
                extracted_data.get("projects")
                or []
            )
        ]

        certification_models = [
            Certification.model_validate(
                certification
            )
            for certification in (
                extracted_data.get("certifications")
                or []
            )
        ]

        return CandidateModel(
            resume_id=resume_id,
            personal_info=extracted_data.get(
                "personal_info",
                {},
            ),
            skills=skills,
            normalized_skills=normalized_skills,
            education=education_models,
            experience=experience_models,
            projects=project_models,
            certifications=certification_models,
            faiss_id=faiss_id,
        )

    def _generate_faiss_id(self) -> int:
        import time

        return int(
            time.time() * 1000
        ) % (2**63 - 1)

    def _insert_candidate(
        self,
        candidate: CandidateModel,
    ) -> str:

        result = self.candidates_col.insert_one(
            candidate.model_dump(
                by_alias=True,
                exclude={"id"},
            )
        )

        return str(
            result.inserted_id
        )

    def _update_resume_status(
        self,
        resume_id: str,
        status: str,
        data: dict | None = None,
    ) -> None:

        update_data = {
            "upload_status": status,
        }

        if data is not None:
            update_data[
                "extracted_data"
            ] = data

        self.resumes_col.update_one(
            {
                "_id": ObjectId(
                    resume_id
                ),
            },
            {
                "$set": update_data,
            },
        )