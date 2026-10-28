import sys
from loguru import logger
from app.core.config.settings import settings
from app.core.logger.redaction import redaction_patcher


def setup_logger() -> None:
    logger.remove()

    logger.configure(patcher=redaction_patcher)

    # diagnose=False: loguru would otherwise print local variable
    # values in tracebacks, which leaked full candidate contact data.
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        backtrace=False,
        diagnose=False,
    )

    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=False,
        diagnose=False,
    )
