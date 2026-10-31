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

    # Confidence of an extracted CV (0..1, see docs/evaluation/confidence.md).
    # Below LOW_CONFIDENCE_WARNING the resume gets the "low_confidence"
    # warning; below REVIEW_BELOW_CONFIDENCE it is held as needs_review
    # instead of being indexed (0 keeps every readable CV indexed).
    LOW_CONFIDENCE_WARNING: float = 0.5

    REVIEW_BELOW_CONFIDENCE: float = 0.0

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

    # Memory (MB) for the model state after the fixed instructions of each
    # prompt, so they are read once instead of for every resume. 0 turns it off.
    LLM_PREFIX_CACHE_MB: int = 1024

    # Extra directory of vocabulary files (*.json) merged with the built-in
    # ones: more languages, or a field's own job titles and employer words.
    VOCABULARY_DIR: Optional[str] = None

    # Second-stage reranking of the best matches with a cross-encoder (see
    # docs/evaluation/ranking_quality.md). Off by default: it adds a model
    # download and about one model run per reranked candidate per request.
    RERANKER_ENABLED: bool = False

    RERANKER_MODEL: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    # How many of the best candidates are reranked, and how much of the final
    # score comes from the cross-encoder (0 = none, 1 = all of it).
    RERANKER_TOP_N: int = 50

    RERANKER_WEIGHT: float = 0.25

    # Read regular experience/education/summary sections with rules and
    # ask the model only when a layout is not understood.
    EXTRACTION_RULES_FIRST: bool = True

    # Answers kept in memory so an identical prompt is not run twice.
    LLM_RESULT_CACHE_SIZE: int = 256

    FAISS_INDEX_PATH: str = (
        "faiss_index/candidate.index"
    )

    FAISS_SAVE_EVERY: int = 1

    # Vector index of the jobs, used to recommend jobs to a candidate.
    JOB_FAISS_INDEX_PATH: str = "faiss_index/job.index"

    # Index a job's vector when it is created (turn off for tools and tests).
    JOB_INDEXING_ENABLED: bool = True

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