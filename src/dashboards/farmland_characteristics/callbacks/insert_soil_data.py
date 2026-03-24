import logging
import re
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
    def clean_column_name(name: str) -> str:
        # This function removes units from soil quantities for INSERT.
        return re.sub(r"\s*\([^)]*\)", "", name).strip().replace(" ", "_").lower()

    @app.callback(
        Output("insert_soil_data_notification", "children"),
        Output("insert_soil_data_notification", "color"),
        Output("insert_soil_data_notification", "is_open"),
        Input("insert_soil_data", "n_clicks"),
        State("token_store", "data"),
        State("isda_soil_data", "data"),
        prevent_initial_call=True
    )
    def insert_soildata(n_clicks: int, token: str, stored_data: list[dict[str, Any]]) -> tuple[str, str, bool]:
        """
        This function INSERTs the iSDA soil data to the `soildata` table in
        the Supabase database.

        Args: (i) n_clicks - triggered by mouse click
            (ii) token - login access token
            (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        table_name = "soildata"
        texture_class_to_int = {
            "Sand": 1,
            "Loamy Sand": 2,
            "Sandy Loam": 3,
            "Loam": 4,
            "Silt Loam": 5,
            "Silt": 6,
            "Sandy Clay Loam": 7,
            "Clay Loam": 8,
            "Silty Clay Loam": 9,
            "Sandy Clay": 10,
            "Silty Clay": 11,
            "Clay": 12
        }  # USDA texture classification conversions

        try:
            if USE_LOCAL_DB:

                # ====== Local PostgreSQL mode ====== #

                conn = db_connect()
                with conn.cursor() as cursor:
                    dataset = stored_data

                    logging.info(f"Processing {table_name}: {type(dataset)} -> {dataset[:2] if dataset else 'Empty'}")

                    if not isinstance(dataset[0], dict):
                        raise TypeError(f"Expected list of dicts for {table_name}, got {type(dataset[0])}")

                    for row in dataset:
                        # Add a timestamp
                        row = {clean_column_name(k): v for k, v in row.items()}  # Remove units from column names
                        row.setdefault("created_at", datetime.now().isoformat())

                        if not isinstance(row["texture_class"], int):
                            # Check if texture class is a string or integer
                            # DB stores it as integer
                            texture_class = row["texture_class"]
                            row["texture_class"] = texture_class_to_int[texture_class]

                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['%s'] * len(row))
                        values = tuple(row.values())

                        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        cursor.execute(query, values)

                return f"✅ {table_name}: Inserted {len(dataset)} rows (Local DB).", "success", True
            else:

                # ====== Supabase mode ====== #

                client = get_supabase_client()

                dataset = []
                for item in stored_data:
                    # Clean keys
                    cleaned_item = {clean_column_name(k): v for k, v in item.items()}
                    cleaned_item.setdefault("created_at", datetime.now().isoformat())

                    if not isinstance(cleaned_item.get("texture_class"), int):
                        texture_class = cleaned_item["texture_class"]
                        cleaned_item["texture_class"] = texture_class_to_int[texture_class]

                    dataset.append(cleaned_item)

                response = client.table(table_name).insert(dataset).execute()

                if response.data:
                    return f"Inserted {len(response.data)} polygons successfully.", "success", True
                else:
                    return f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}", "danger", True

        except Exception as e:
            logger.error(f"Error inserting polygons: {e}")
            return f"❌ Insert failed: {e}", "danger", True