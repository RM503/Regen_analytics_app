"""
Module for db data inserts for working across all dashboard tables.
Handles inserts for both single and multi-table operations. Insert
logic is valid for local and Supabase modes.

Defines pseudo-private functions for handling inserts in local and
Supabase modes.
"""
from __future__ import annotations

import datetime
from typing import Any

from postgrest.base_request_builder import APIResponse
from psycopg2.errors import OperationalError
from psycopg2.extensions import cursor as _cursor
from supabase import Client

from .db_client import get_supabase_client, local_db_connection
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Custom type annotations
SingleTableRows = list[dict[str, Any]]
MultiTableRows = dict[str, list[dict[str, Any]]]
DbInsertReturn = tuple[str, str, bool]


INSERT_ERROR_MSG = (
    "❌ Data passed for insert is of incorrect type. Either rows are not."
    "Either rows are not passed as a list or one or more row entities are not dictionaries."
)


# Insert logic
def _insert_local_table(dataset: SingleTableRows, table_name: str, cursor: _cursor) -> None:
    """
    Inserts rows for a single table in local DB.

    Args:
        dataset (SingleTableRows): rows of the single table dataset to be inserted.
        table_name (str): name of the table to be inserted.
        cursor (Cursor): cursor object to be used to execute insert operations.

    Returns:
        None
    """
    for row in dataset:
        row.setdefault("created_at", datetime.datetime.now().isoformat())
        columns = ', '.join(row.keys())
        placeholders = ', '.join(['%s'] * len(row))
        values = tuple(row.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)


def _insert_supabase_table(
        dataset: SingleTableRows,
        table_name: str,
        client: Client
    ) -> APIResponse[dict[str, Any]]:
    """
    Inserts rows for a single table in Supabase.

    Args:
        dataset (SingleTableRows): rows of the single table dataset to be inserted.
        table_name (str): name of the table to be inserted.
        client (Client): client object to be used to execute insert operations.

    Returns:
        (APIResponse[dict[str, Any]]): response of the insert operations.
    """
    for item in dataset:
        item["created_at"] = datetime.datetime.now().isoformat()

    response = client.table(table_name).insert(dataset).execute()
    return response


def _row_instance_check(stored_data: SingleTableRows) -> bool:
    return (
        isinstance(stored_data, list) and all(isinstance(data, dict) for data in stored_data)
    )


def local_db_insert_single(stored_data: SingleTableRows, table_name: str) -> DbInsertReturn:
    """
    Single table inserts for local DBs.

    Args:
        stored_data (SingleTableRows): rows of the single table dataset to be inserted.
        table_name (str): name of the table to be inserted.

    Returns:
        (DbInsertReturn): message indicating insert result.
    """
    if not _row_instance_check(stored_data):
        return INSERT_ERROR_MSG, "warning", True

    try:
        with local_db_connection() as conn:
            with conn.cursor() as cursor:
                dataset = stored_data

                _insert_local_table(dataset, table_name, cursor)

        logger.info(f"Inserted {len(dataset)} rows successfully to local DB.")
        return f"✅ Inserted {len(dataset)} rows successfully to local DB.", "success", True
    except OperationalError as e:
        logger.error(f"Error inserting {table_name} to local DB failed: {e}")
        return f"❌ Error inserting {table_name} to local DB.", "warning", True


def supabase_db_insert_single(stored_data: SingleTableRows, table_name: str) -> DbInsertReturn:
    if not _row_instance_check(stored_data):
        return INSERT_ERROR_MSG, "warning", True

    try:
        dataset = stored_data
        client = get_supabase_client()
        _ = _insert_supabase_table(stored_data, table_name, client)

        logger.info(f"Inserted {len(dataset)} rows successfully to Supabase.")
        return f"✅ Inserted {len(dataset)} rows successfully to Supabase.", "success", True

    except OperationalError as e:
        logger.error(f"Error inserting {table_name} to Supabase failed: {e}")
        return f"❌ Error inserting {table_name} to Supabase.", "warning", True


def local_db_insert_multi(stored_data: MultiTableRows, table_names: list[str]) -> DbInsertReturn:
    """
    Inserts rows of multi-table dataset into local DB.

    Args:
        stored_data (MultiTableRows): rows of the multi-table dataset to be inserted.
        table_names (list[str]): list of table names to be inserted.

    Returns:
        (DbInsertReturn[dict[str, Any]]): response of the insert operations.
    """
    messages = []
    with local_db_connection() as conn:
        with conn.cursor() as cursor:
            for table_name in table_names:
                dataset = stored_data[table_name]

                if not dataset:
                    continue
                if not isinstance(dataset[0], dict):
                    raise TypeError(f"Expected list of dicts for {table_name}, got {type(dataset[0])} instead.")

                _insert_local_table(dataset, table_name, cursor)

                messages.append(f"✅ {table_name}: Inserted {len(dataset)} rows to local DB.")

    return " | ".join(messages), "success", True


def supabase_db_insert_multi(stored_data: MultiTableRows, table_names: list[str]) -> DbInsertReturn:
    """
    Inserts rows of multi-table dataset into Supabase.

    Args:
        stored_data (MultiTableRows): rows of the multi-table dataset to be inserted.
        table_names (list[str]): list of table names to be inserted.

    Returns:
        (DbInsertReturn[dict[str, Any]]): response of the insert operations.
    """
    messages = []
    client = get_supabase_client()

    for table_name in table_names:
        dataset = stored_data[table_name]

        if not dataset:
            continue

        response = _insert_supabase_table(dataset, table_name, client)

        if response.data:
            messages.append(f"✅ {table_name}: Inserted {len(dataset)} rows to Supabase DB.")

    if messages:
        return " | ".join(messages), "success", True
    else:
        return "⚠️ No data to insert.", "warning", True
