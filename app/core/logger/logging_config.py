import sys
from loguru import logger
from app.core.config.settings import settings
from app.core.logger.redaction import redaction_patcher

# Bound per request / per job with logger.contextualize; "-" outside of one.
CONTEXT_DEFAULTS = {"request_id": "-", "resume_id": "-"}

TEXT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{extra[request_id]} {extra[resume_id]} - <level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | "
    "{extra[request_id]} {extra[resume_id]} - {message}"
)


def setup_logger() -> None:
    logger.remove()

    logger.configure(patcher=redaction_patcher, extra=CONTEXT_DEFAULTS)

    # diagnose=False: loguru would otherwise print local variable
    # values in tracebacks, which leaked full candidate contact data.
    if settings.LOG_FORMAT == "json":
        # One JSON object per line, with request_id and resume_id as fields,
        # for log collectors.
        logger.add(
            sys.stdout,
            serialize=True,
            level=settings.LOG_LEVEL,
            backtrace=False,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stdout,
            colorize=True,
            format=TEXT_FORMAT,
            level=settings.LOG_LEVEL,
            backtrace=False,
            diagnose=False,
        )

    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format=FILE_FORMAT,
        backtrace=False,
        diagnose=False,
    )
