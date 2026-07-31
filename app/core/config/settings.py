from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "resume_mining_db"
    
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "faiss_index/candidate.index"
    
    LOG_LEVEL: str = "INFO"
    
    hf_token: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()