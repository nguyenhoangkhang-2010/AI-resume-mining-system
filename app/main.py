from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config.settings import settings
from app.core.logger.logging_config import setup_logger
from app.core.security.startup import validate_security_settings
from app.database.mongodb.connection import mongo_db
from app.database.vector_db.faiss_manager import FaissManager
from app.api.router import api_router

from app.core.auth.huggingface import login_huggingface

from app.api.exceptions import register_exception_handlers

from app.api.security import require_admin
from app.bootstrap import (
    build_processing_stack,
    build_queue,
    build_worker,
    start_warm_up,
)
from app.core.observability import metrics
from app.core.observability.request_context import observe_request


setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting up AI Resume Mining System API..."
    )

    # Before any model is loaded: stop at once if authentication is
    # required but not configured.
    validate_security_settings(settings)

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

    stack = build_processing_stack()

    for name, value in stack.state().items():
        setattr(app.state, name, value)

    app.state.worker = None

    if settings.PROCESSING_MODE == "queue":
        queue = build_queue()
        app.state.queue = queue

        if settings.METRICS_ENABLED:
            metrics.watch_queue(queue.stats)

        if settings.WORKER_EMBEDDED:
            app.state.worker = build_worker(stack.resume_service, queue)
            app.state.worker.start()

    if settings.WARMUP_ENABLED:
        start_warm_up(app.state)
    else:
        app.state.warm = True

    logger.success(
        "Resume processing pipeline initialized successfully."
    )

    yield

    logger.info(
        "Shutting down API..."
    )

    if app.state.worker is not None:
        app.state.worker.stop()

    FaissManager.shutdown()

    mongo_db.close()


app = FastAPI(
    title="AI Resume Mining & Candidate Matching System",
    description="Production-ready REST APIs for intelligent resume parsing, matching and ranking.",
    version="1.0.0",
    lifespan=lifespan
)

register_exception_handlers(app)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    return await observe_request(request, call_next)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")

    # Responses carry personal data: do not let browsers or proxies keep them.
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")

    return response


cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

# Added last so it is the outermost middleware and answers preflight
# requests itself. Keys travel in headers, so no cookies are needed.
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

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


@app.get("/ready", tags=["Health"])
async def readiness_check(request: Request) -> JSONResponse:
    """
    Ready to take traffic: the database answers, the models are loaded and,
    when this process runs the queue worker, the worker threads are alive.
    """

    database_up = await run_in_threadpool(mongo_db.ping)
    models_loaded = (
        getattr(request.app.state, "resume_service", None) is not None
        and getattr(request.app.state, "warm", True)
    )
    worker = getattr(request.app.state, "worker", None)
    worker_up = worker is None or worker.alive

    ready = database_up and models_loaded and worker_up

    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "database": "connected" if database_up else "disconnected",
            "models": "loaded" if models_loaded else "loading",
            "worker": "n/a" if worker is None else ("running" if worker_up else "stopped"),
        },
    )


if settings.METRICS_ENABLED:

    @app.get("/metrics", tags=["Health"], include_in_schema=False)
    def metrics_endpoint(_: object = Depends(require_admin)) -> Response:
        body, content_type = metrics.render()

        return Response(content=body, media_type=content_type)
