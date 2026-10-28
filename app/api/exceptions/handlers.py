from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from pymongo.errors import ConnectionFailure

from app.core.exceptions import AppError, DatabaseUnavailableError


def _error_response(
    status_code: int,
    detail: str,
    code: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "code": code,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def handle_app_error(
        request: Request,
        exc: AppError,
    ):
        logger.warning(
            "{} {} -> {} {}",
            request.method,
            request.url.path,
            exc.status_code,
            exc.message,
        )

        return _error_response(
            exc.status_code,
            exc.message,
            exc.code,
        )

    @app.exception_handler(ConnectionFailure)
    async def handle_database_connection_failure(
        request: Request,
        exc: ConnectionFailure,
    ):
        logger.error(
            "{} {} -> database connection failure: {}",
            request.method,
            request.url.path,
            exc,
        )

        return _error_response(
            DatabaseUnavailableError.status_code,
            DatabaseUnavailableError.default_message,
            DatabaseUnavailableError.code,
        )

    @app.exception_handler(Exception)
    async def handle_exception(
        request: Request,
        exc: Exception,
    ):
        logger.opt(exception=exc).error(
            "Unhandled error on {} {}",
            request.method,
            request.url.path,
        )

        return _error_response(
            500,
            "Internal server error",
            AppError.code,
        )
