import time
from bson import ObjectId
from loguru import logger

from app.database.mongodb.connection import mongo_db
from app.models.resume import ResumeModel
from app.models.candidate import CandidateModel
from app.schemas.resume_schema import ResumeResponse
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.embeddings.services.embedding_service import EmbeddingService
from app.vector_store.vector_store import VectorStore


class ResumeService:
    
    def __init__(self):
        self.resume_pipeline = ResumePipeline()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    @property
    def db(self):
        return mongo_db.get_db()
        
    @property
    def resumes_col(self):
        return self.db["resumes"]
        
    @property
    def candidates_col(self):
        return self.db["candidates"]

    def process_uploaded_resume(self, file_path: str, filename: str) -> ResumeResponse:
        logger.info(f"Orchestrating processing for resume: {filename}")
        
        resume = ResumeModel(filename=filename, file_path=file_path, upload_status="pending")
        resume.id = self._insert_resume(resume)
        
        try:
            cleaned_text = self.resume_pipeline.process_pdf(file_path)
            
            # TODO: Replace this mock with a real call to the ExtractionEngine
            skills = ["Python", "Data Science", "Machine Learning"]
            personal_info = {"name": "Candidate Doe", "email": "doe@example.com"}
            
            # --- Start: Optimize Embedding Content ---
            # Instead of embedding the entire raw text, embed only the extracted skills.
            embedding_text = " ".join(skills)
            embedding = self.embedding_service.generate_embedding(embedding_text)
            # --- End: Optimize Embedding Content ---
            
            faiss_id = self._generate_faiss_id()
            self.vector_store.add_candidate_embedding(faiss_id=faiss_id, embedding=embedding)
            
            candidate = CandidateModel(
                resume_id=resume.id,
                personal_info=personal_info,
                skills=skills,
                faiss_id=faiss_id
            )
            self._insert_candidate(candidate)
            
            self._update_resume_status(resume.id, "processed", cleaned_text)
            resume.upload_status = "processed"
            
            logger.success(f"Resume {filename} processed and indexed successfully.")
            return ResumeResponse.model_validate(resume)
            
        except Exception as e:
            logger.error(f"Pipeline failed for resume {filename}: {e}")
            self._update_resume_status(resume.id, "failed")
            raise e

    def _generate_faiss_id(self) -> int:
        return int(time.time() * 1000) % (2**63 - 1)
        
    def _insert_resume(self, resume: ResumeModel) -> str:
        res = self.resumes_col.insert_one(resume.model_dump(by_alias=True, exclude={"id"}))
        return str(res.inserted_id)
        
    def _insert_candidate(self, candidate: CandidateModel) -> str:
        res = self.candidates_col.insert_one(candidate.model_dump(by_alias=True, exclude={"id"}))
        return str(res.inserted_id)
        
    def _update_resume_status(self, resume_id: str, status: str, text: str = None):
        update_data = {"upload_status": status}
        if text: update_data["raw_text"] = text
        self.resumes_col.update_one({"_id": ObjectId(resume_id)}, {"$set": update_data})