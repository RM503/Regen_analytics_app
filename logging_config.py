import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logging():
    os.makedirs("logs", exist_ok=True)

    gunicorn_error_logger = logging.getLogger("gunicorn.error")

    if gunicorn_error_logger.handlers:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Add Gunicorn handlers first (to keep access logs etc)
        for handler in gunicorn_error_logger.handlers:
            root_logger.addHandler(handler)

        # Now add your rotating file handler in addition
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    else:
        # No Gunicorn, standalone mode
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(stream_handler)
        root_logger.addHandler(file_handler)

    # Set levels for noisy loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask.app").setLevel(logging.INFO)
    logging.getLogger("dash").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info("Logging configured with Gunicorn integration and file handler.")
