import logging
from datetime import datetime
from typing import Any

from dash import Input, Output, State

from auth.supabase_auth import get_supabase_client
from config import USE_LOCAL_DB, LOCAL_DB_CONFIG
from db.db_utils import db_connect

logger = logging.getLogger(__name__)

if USE_LOCAL_DB:
    logger.info(
        f"Running in LOCAL mode — connecting to PostgreSQL at "
        f"{LOCAL_DB_CONFIG['host']}:{LOCAL_DB_CONFIG['port']}, "
        f"database '{LOCAL_DB_CONFIG['database']}'."
    )
else:
    logger.info("Running in SUPABASE mode.")

def register(app):
    @app.callback(
        Output("insert_farm_stats_notification", "children"),
        Output("insert_farm_stats_notification", "color"),
        Output("insert_farm_stats_notification", "is_open"),
        Input("insert_farm_stats", "n_clicks"),
        State("token_store", "data"),
        State("farm_stats", "data"),
        prevent_initial_call=True
    )
    def run(n_clicks: int, token: str, stored_data: list[dict[str, Any]]) -> tuple[str, str, bool]:
        """
        This function performs an INSERT of all the farm stat tables stored in
        the `farm_stats` dcc.Store. Depending on `USE_LOCAL_DB` it will either
        INSERT the data to a local PostgreSQL database or Supabase (the former is)
        for testing purposes.

        Args: (i) n_clicks - triggered by mouse click
              (ii) token - login access token
              (iii) stored_data - list of datatables stored in dcc.Store

        Returns: Status message of the insert operation
        """

        # List of data tables stored in dcc.Store
        tables = ["highndmidays", "peakvidistribution", "ndvipeaksperfarm"]

        messages = []

        try:

            if USE_LOCAL_DB:
                conn = db_connect()

                # ====== Local PostgreSQL mode ====== #

                with conn.cursor() as cursor:
                    for TABLE in tables:
                        dataset = stored_data[f"df_{TABLE}"]

                        logging.info(f"Processing {TABLE}: {type(dataset)} -> {dataset[:2] if dataset else 'Empty'}")

                        if not dataset:
                            continue

                        if not isinstance(dataset[0], dict):
                            raise TypeError(f"Expected list of dicts for {TABLE}, got {type(dataset[0])}")

                        for row in dataset:
                            # Add a timestamp
                            row.setdefault("created_at", datetime.now().isoformat())

                            columns = ', '.join(row.keys())
                            placeholders = ', '.join(['%s'] * len(row))
                            values = tuple(row.values())

                            query = f"INSERT INTO {TABLE} ({columns}) VALUES ({placeholders})"
                            cursor.execute(query, values)

                        messages.append(f"✅ {TABLE}: Inserted {len(dataset)} rows (Local DB).")

                return " | ".join(messages), "success", True

            else:
                client = get_supabase_client()

                # ====== Supabase mode ====== #

                for TABLE in tables:
                    dataset = stored_data[f"df_{TABLE}"]  # data corresponding to particular table
                    if dataset:
                        for item in dataset:
                            item["created_at"] = datetime.now().isoformat()

                        response = client.table(TABLE).insert(dataset).execute()

                        if response.data:
                            messages.append(f"✅ {TABLE}: Inserted {len(response.data)} rows.")
                        else:
                            messages.append(
                                f"❌ {TABLE}: Insert failed ({getattr(response, 'error', 'Unknown error')})."
                            )

                if messages:
                    return " | ".join(messages), "success", True
                else:
                    return "⚠️ No data to insert.", "warning", True

        except Exception as e:
            logger.error(f"Insert error: {e}")
            return f"❌ Error inserting data: {e}", "danger", True