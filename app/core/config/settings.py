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

    # --- Security ---------------------------------------------------------
    # API keys as comma-separated role:key pairs, e.g.
    #   API_KEYS=admin:<long random key>,user:<another long random key>
    # Roles: admin (everything, including delete) and user (everything else).
    # With AUTH_ENABLED=true the API refuses to start without a valid key.
    AUTH_ENABLED: bool = True

    API_KEYS: Optional[str] = None

    # Browser origins allowed to call the API, comma-separated. Empty means
    # no cross-origin access.
    CORS_ORIGINS: str = ""

    RATE_LIMIT_ENABLED: bool = True

    RATE_LIMIT_PER_MINUTE: int = 120

    # Stricter limit for endpoints that run the embedding model or the LLM.
    RATE_LIMIT_HEAVY_PER_MINUTE: int = 20

    MAX_JOB_DESCRIPTION_CHARS: int = 50000

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

    # Never run code shipped with a model unless you have reviewed it.
    NER_TRUST_REMOTE_CODE: bool = False

    NER_CONFIDENCE_THRESHOLD: float = 0.70
    
    LLM_PROVIDER: str = "huggingface"

    LLM_DEVICE: int = -1

    MAX_NEW_TOKENS: int = 128

    LLM_DO_SAMPLE: bool = False

    LLM_MAX_INPUT_CHARS: int = 12000

    # Output limits per extractor. Too low and the model's JSON is cut
    # off, which loses entries; generation time grows with the limit.
    LLM_EXPERIENCE_MAX_TOKENS: int = 360

    LLM_EDUCATION_MAX_TOKENS: int = 256

    LLM_PROJECTS_MAX_TOKENS: int = 768

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

    # Answers for headings the lexicon does not know (kept next to the index).
    HEADING_CACHE_PATH: str = "faiss_index/heading_cache.json"

    LOG_LEVEL: str = "INFO"

    hf_token: Optional[str] = None

    skill_alias_path: str = (
        "data/dictionaries/skill_aliases.json"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()