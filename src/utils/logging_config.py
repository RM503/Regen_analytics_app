import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_FILE = ROOT_DIR / "logs" / "app.log"
_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def setup_logging(
    level: str | int | None = None,
    *,
    log_to_file: bool | None = None,
    log_file: str | Path = DEFAULT_LOG_FILE,
) -> None:
    resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)

    if log_to_file is None:
        log_to_file = os.getenv("LOG_TO_FILE", "1").lower() in {"1", "true", "yes"}

    root_logger = logging.getLogger()
    if getattr(root_logger, "_regen_logging_configured", False):
        root_logger.setLevel(resolved_level)
        return

    root_logger.setLevel(resolved_level)
    formatter = logging.Formatter(_FORMAT)

    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    if gunicorn_error_logger.handlers:
        for handler in gunicorn_error_logger.handlers:
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
    else:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    if log_to_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.INFO)
    logging.getLogger("flask.app").setLevel(logging.INFO)

    root_logger._regen_logging_configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)