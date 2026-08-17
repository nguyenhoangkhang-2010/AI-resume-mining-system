from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"

    DB_NAME: str = "resume_mining_db"

    MODEL_NAME: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    LLM_MODEL_NAME: str = (
        "mistralai/Mistral-7B-Instruct-v0.2"
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
    
    LLM_PROVIDER: str = "huggingface"

    LLM_DEVICE: int = -1

    MAX_NEW_TOKENS: int = 128

    LLM_DO_SAMPLE: bool = False

    LLM_MAX_INPUT_CHARS: int = 12000

    LLM_GGUF_MODEL_PATH: str = (
        "models/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
    )

    LLM_GGUF_CONTEXT_SIZE: int = 6144

    LLM_GGUF_THREADS: int = 0

    LLM_GGUF_GPU_LAYERS: int = 0

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