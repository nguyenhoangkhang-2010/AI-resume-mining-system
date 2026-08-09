from bson import ObjectId
from loguru import logger
from datetime import datetime

from app.database.mongodb.connection import mongo_db
from app.models.job import JobModel
from app.schemas.job_schema import JobCreateRequest, JobResponse
from app.extraction.extraction_engine import ExtractionEngine


class JobService:    
    def __init__(self):
        self.extraction_engine = ExtractionEngine()

    @property
    def db(self):
        return mongo_db.get_db()
        
    @property
    def jobs_col(self):
        return self.db["jobs"]

    def create_job(self, request: JobCreateRequest) -> JobResponse:
        logger.info(f"Creating job: '{request.title}'")
        
        # Use the JobPipeline for comprehensive extraction
        job_data = self.extraction_engine.extract_job_description(request.description)
        
        job_model = JobModel(
            title=request.title,
            raw_text=request.description,  # Store original description as raw_text
            description=job_data.get("description", request.description), # LLM-extracted description or original
            required_skills=job_data.get("required_skills", []),
            normalized_skills=job_data.get("normalized_skills", []),
            experience_years=job_data.get("experience_years"),
            responsibilities=job_data.get("responsibilities", []),
            occupation=job_data.get("occupation"),
            faiss_id=None,
        )
        
        job_id = self._save_job(job_model)
        job_model.id = job_id
        
        logger.success(f"Successfully created and indexed job (ID: {job_id})")
        return JobResponse.model_validate(job_model)
    
    def _save_job(self, job: JobModel) -> str:
        result = self.jobs_col.insert_one(job.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)