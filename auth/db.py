# Script for creating a direct connection to database for `SELECT` commands

import logging
import os

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

dotenv.load_dotenv(override=True)
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is not set.")

try:
    engine = create_engine(DB_URL, echo=False)
    logger.info("SQLAlchemy engine created successfully.")
except OperationalError as e:
    logger.warning(f"SQLAlchemy connection failed: {e}")
    engine = None
