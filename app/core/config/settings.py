from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"

    DB_NAME: str = "resume_mining_db"

    MODEL_NAME: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    LLM_MODEL_NAME: str = (
        "Qwen/Qwen2.5-1.5B-Instruct"
    )
    
    NER_PRIMARY_MODEL: str = (
        "oksomu/resume-ner"
    )

    NER_MULTILINGUAL_MODEL: str = (
        "Davlan/xlm-roberta-base-wikiann-ner"
    )

    NER_PRIMARY_ENABLED: bool = True

    NER_MULTILINGUAL_ENABLED: bool = True

    NER_DEVICE: str = "cpu"

    NER_TRUST_REMOTE_CODE: bool = True

    NER_CONFIDENCE_THRESHOLD: float = 0.70

    LLM_PROVIDER: str = (
        "huggingface"
    )

    MAX_NEW_TOKENS: int = 256

    FAISS_INDEX_PATH: str = (
        "faiss_index/candidate.index"
    )

    LOG_LEVEL: str = "INFO"

    hf_token: Optional[str] = None

    skill_alias_path: str = (
        "data/dictionaries/skill_aliases.json"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()