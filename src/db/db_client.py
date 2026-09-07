"""
Module for initializing db runtimes
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

import psycopg2
from flask import session
from psycopg2.extensions import connection as Psycopg2Connection
from supabase import Client, create_client

from config import LOCAL_DB_CONFIG, USE_LOCAL_DB
from auth.supabase_auth import SUPABASE_KEY, SUPABASE_URL
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Database modes - must be either 'local' or 'supabase'
DbMode = Literal["local", "supabase"]


@dataclass(frozen=True)
class DbRuntime:
    mode: DbMode


def get_db_runtime() -> DbRuntime:
    """
    Resolves the active database mode once for inserts.

    Local mode uses Psycopg2 for connections while Supabases uses
    the authenticated Supabse connection.
    """
    if USE_LOCAL_DB:
        logger.debug("Running in LOCAL mode - connecting to PostgreSQL at "
            "%s:%s, database '%s'.",
            LOCAL_DB_CONFIG["host"],
            LOCAL_DB_CONFIG["port"],
            LOCAL_DB_CONFIG["database"]
        )

        return DbRuntime(mode="local")

    logger.debug("Running in Supabase mode.")
    return DbRuntime(mode="supabase")


@contextmanager
def local_db_connection() -> Iterator[Psycopg2Connection]:
    """
    Establishes a local PostgreSQL database connection using the
    Psycopg2Connection object.
    """
    conn: Psycopg2Connection | None = None

    try:
        conn = psycopg2.connect(**LOCAL_DB_CONFIG)
        yield conn
        conn.commit()

    except psycopg2.OperationalError as e:
        if conn is not None:
            conn.rollback()

        logger.exception("Could not connect to PostgreSQL database.")
        raise RuntimeError("Could not connect to PostgreSQL database") from e

    except Exception as e:
        if conn is not None:
            conn.rollback()

        logger.exception("An unexpected error occurred.")
        raise e

    finally:
        if conn is not None:
            conn.close()


def get_supabase_client() -> Client:
    """
    Establishes a Supabase client using the current Flask session access token.
    """
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL not set")

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY not set")

    token = session.get("access_token")
    if not token:
        raise RuntimeError("SESSION_TOKEN not set")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.postgrest.auth(token)

    return client
