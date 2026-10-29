from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"

    # Credentials can be given separately from the URI, so passwords with
    # characters such as @ or : need no URL-encoding.
    MONGO_USERNAME: Optional[str] = None

    MONGO_PASSWORD: Optional[str] = None

    MONGO_AUTH_SOURCE: str = "admin"

    DB_NAME: str = "resume_mining_db"

    MAX_UPLOAD_MB: int = 10

    # OCR for scanned (image-only) PDFs. Needs the Tesseract program and its
    # language data installed; when it is missing the page stays empty and the
    # resume is flagged needs_review.
    OCR_ENABLED: bool = False

    OCR_LANGUAGES: str = "eng+vie"

    OCR_DPI: int = 300

    DB_REQUIRED_AT_STARTUP: bool = False

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

    FAISS_SAVE_EVERY: int = 1

    LOG_LEVEL: str = "INFO"

    hf_token: Optional[str] = None

    skill_alias_path: str = (
        "data/dictionaries/skill_aliases.json"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()