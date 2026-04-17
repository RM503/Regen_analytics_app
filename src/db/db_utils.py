import psycopg2
from psycopg2.extensions import connection
from config import LOCAL_DB_CONFIG

from utils.logging_config import get_logger

logger = get_logger(__name__)

def db_connect() -> connection | None:
    try:
        conn = psycopg2.connect(**LOCAL_DB_CONFIG)
        conn.autocommit = True
        return conn 
    except psycopg2.Error as e:
        logger.error(f"Error connecting to local PostgreSQL database; {e}")
        return None