import psycopg2
from psycopg2.extensions import connection
from config import LOCAL_DB_CONFIG
import logging 

logging.basicConfig(level=logging.INFO)

def db_connect() -> connection | None:
    try:
        conn = psycopg2.connect(**LOCAL_DB_CONFIG)
        conn.autocommit = True
        return conn 
    except psycopg2.Error as e:
        logging.error(f"Error connecting to local PostgreSQL database; {e}")
        return None