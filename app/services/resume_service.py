import time

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
from app.schemas.resume_schema import ResumeResponse
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.models.resume import ResumeModel
from app.embeddings.services.embedding_service import EmbeddingService
from app.vector_store.vector_store import VectorStore
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)


class ResumeService:

    def __init__(
        self,
        resume_pipeline: ResumePipeline,
    ):
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

    def create_resume(
        self,
        file_path: str,
        filename: str,
    ) -> ResumeResponse:

        logger.info(
            "Creating resume processing job for: {}",
            filename,
        )

        resume = ResumeModel(
            filename=filename,
            file_path=file_path,
            upload_status="pending",
        )

        resume.id = self._insert_resume(
            resume
        )

        logger.success(
            "Resume job created successfully: {}",
            resume.id,
        )

        return ResumeResponse.model_validate(
            resume
        )

    def process_resume(
        self,
        resume_id: str,
    ) -> None:

        logger.info(
            "Starting background resume processing: {}",
            resume_id,
        )

        try:
            object_id = ObjectId(resume_id)

            resume_document = self.resumes_col.find_one(
                {
                    "_id": object_id,
                }
            )

            if not resume_document:
                logger.error(
                    "Resume not found for processing: {}",
                    resume_id,
                )
                return

            file_path = resume_document.get(
                "file_path"
            )

            filename = resume_document.get(
                "filename",
                "unknown",
            )

            if not file_path:
                raise ValueError(
                    f"Resume file path is missing: {resume_id}"
                )

            self._update_resume_status(
                resume_id,
                "processing",
            )

            pipeline_start = time.perf_counter()

            logger.info(
                "Running resume AI pipeline: {}",
                filename,
            )

            extracted_data = (
                self.resume_pipeline.process_pdf(
                    file_path
                )
            )

            logger.info(
                "Resume AI pipeline completed in {:.3f}s: {}",
                time.perf_counter() - pipeline_start,
                filename,
            )

            candidate = self._build_candidate(
                resume_id=resume_id,
                extracted_data=extracted_data,
            )

            self._insert_candidate(
                candidate
            )

            self._update_resume_status(
                resume_id,
                "processed",
                extracted_data,
            )

            logger.success(
                "Resume {} processed and indexed successfully.",
                filename,
            )

        except Exception as e:

            logger.exception(
                "Background resume processing failed for {}: {}",
                resume_id,
                e,
            )

            try:
                self._update_resume_status(
                    resume_id,
                    "failed",
                )
            except Exception as status_error:
                logger.exception(
                    "Failed to update resume {} status to failed: {}",
                    resume_id,
                    status_error,
                )

            raise

    def _build_candidate(
        self,
        resume_id: str,
        extracted_data: dict,
    ) -> CandidateModel:

        skills = extracted_data.get(
            "skills"
        ) or []

        normalized_skills = [
            self.skill_normalizer.normalize(
                skill
            )
            for skill in skills
            if isinstance(
                skill,
                str,
            )
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

        education_data = (
            extracted_data.get(
                "education"
            )
            or []
        )

        education_models = [
            Education.model_validate(
                education
            )
            for education in education_data
        ]

        experience_data = (
            extracted_data.get(
                "experience"
            )
            or []
        )

        experience_models = [
            Experience.model_validate(
                experience
            )
            for experience in experience_data
        ]

        projects_data = (
            extracted_data.get(
                "projects"
            )
            or []
        )

        project_models = [
            Project.model_validate(
                project
            )
            for project in projects_data
        ]

        certifications_data = (
            extracted_data.get(
                "certifications"
            )
            or []
        )

        certification_models = [
            Certification.model_validate(
                certification
            )
            for certification in certifications_data
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

    def _generate_faiss_id(
        self,
    ) -> int:

        return int(
            time.time() * 1000
        ) % (
            2**63 - 1
        )

    def _insert_resume(
        self,
        resume: ResumeModel,
    ) -> str:

        result = self.resumes_col.insert_one(
            resume.model_dump(
                by_alias=True,
                exclude={"id"},
            )
        )

        return str(
            result.inserted_id
        )

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
                )
            },
            {
                "$set": update_data
            },
        )