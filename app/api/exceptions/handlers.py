from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ValueError)
    async def handle_value_error(
        request: Request,
        exc: ValueError,
    ):
        logger.warning(str(exc))

        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def handle_exception(
        request: Request,
        exc: Exception,
    ):
        logger.exception(exc)

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
            },
        )