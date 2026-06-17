from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.core.logger.logging_config import setup_logger
from app.database.mongodb.connection import mongo_db
from app.api.router import api_router

setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up AI Resume Mining System API...")
    try:
        mongo_db.connect()
    except Exception as e:
        logger.critical(f"Database initialization failed during startup: {e}")
    
    yield
    
    logger.info("Shutting down API...")
    mongo_db.close()


app = FastAPI(
    title="AI Resume Mining & Candidate Matching System",
    description="Production-ready REST APIs for intelligent resume parsing, matching and ranking.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root_endpoint() -> dict:
    return {"message": "Welcome to AI Resume Mining & Candidate Matching System API. Visit /docs for Swagger UI."}


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    db_status = "connected" if mongo_db.client is not None else "disconnected"
    app_status = "healthy" if db_status == "connected" else "degraded"
    
    return {
        "status": app_status,
        "database": db_status
    }