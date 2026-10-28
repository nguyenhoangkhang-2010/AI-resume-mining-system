from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config.settings import settings
from app.core.logger.logging_config import setup_logger
from app.database.mongodb.connection import mongo_db
from app.database.vector_db.faiss_manager import FaissManager
from app.api.router import api_router

from app.core.auth.huggingface import login_huggingface

from app.api.exceptions import register_exception_handlers

from app.extraction.llm.llm_extractor import LLMExtractor
from app.extraction.section.section_classifier import SectionClassifier
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.extraction.section.section_detector import SectionDetector
from app.extraction.extraction_engine import ExtractionEngine
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.services.resume_service import ResumeService


setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting up AI Resume Mining System API..."
    )

    login_huggingface()

    try:
        mongo_db.connect()
    except Exception as e:
        logger.critical(
            "Database initialization failed during startup: {}",
            e,
        )

        if settings.DB_REQUIRED_AT_STARTUP:
            raise

    logger.info(
        "Initializing resume processing pipeline..."
    )

    llm_extractor = LLMExtractor()

    section_classifier = SectionClassifier(
        llm_extractor=llm_extractor,
    )

    semantic_classifier = SectionSemanticClassifier()

    section_detector = SectionDetector(
        semantic_classifier=semantic_classifier,
        llm_classifier=section_classifier,
    )

    extraction_engine = ExtractionEngine(
        llm_extractor=llm_extractor,
    )

    resume_pipeline = ResumePipeline(
        section_detector=section_detector,
        extraction_engine=extraction_engine,
    )

    resume_service = ResumeService(
        resume_pipeline=resume_pipeline,
    )

    app.state.llm_extractor = llm_extractor
    app.state.section_classifier = section_classifier
    app.state.semantic_classifier = semantic_classifier
    app.state.section_detector = section_detector
    app.state.extraction_engine = extraction_engine
    app.state.resume_pipeline = resume_pipeline
    app.state.resume_service = resume_service

    logger.success(
        "Resume processing pipeline initialized successfully."
    )

    yield

    logger.info(
        "Shutting down API..."
    )

    FaissManager.shutdown()

    mongo_db.close()


app = FastAPI(
    title="AI Resume Mining & Candidate Matching System",
    description="Production-ready REST APIs for intelligent resume parsing, matching and ranking.",
    version="1.0.0",
    lifespan=lifespan
)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root_endpoint() -> dict:
    return {"message": "Welcome to AI Resume Mining & Candidate Matching System API. Visit /docs for Swagger UI."}


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    database_up = await run_in_threadpool(mongo_db.ping)

    return JSONResponse(
        status_code=200 if database_up else 503,
        content={
            "status": "healthy" if database_up else "degraded",
            "database": "connected" if database_up else "disconnected",
        },
    )
