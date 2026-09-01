import logging
from logging.handlers import RotatingFileHandler

from salesflow.config import LOG_DIR, ensure_directories


def configure_logging() -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger("salesflow")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / "pipeline.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger