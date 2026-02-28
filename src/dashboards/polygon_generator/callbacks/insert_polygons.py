import datetime
import logging
from typing import Any

from dash import Input, Output, State

from auth.supabase_auth import get_supabase_client
from config import USE_LOCAL_DB, LOCAL_DB_CONFIG
from db.db_utils import db_connect

logger = logging.getLogger(__name__)

if USE_LOCAL_DB:
    logging.info(
        f"Running in LOCAL mode — connecting to PostgreSQL at "
        f"{LOCAL_DB_CONFIG['host']}:{LOCAL_DB_CONFIG['port']}, "
        f"database '{LOCAL_DB_CONFIG['database']}'."
    )
else:
    logging.info("Running in SUPABASE mode.")

def register(app):
    @app.callback(
            Output("insert_notification", "children"),
            Output("insert_notification", "color"),
            Output("insert_notification", "is_open"),
            Input("insert_button", "n_clicks"),
            State("token_store", "data"),
            State("polygons_store", "data"),
            prevent_initial_call=True
        )
    def run(n_clicks: int, token: str, stored_data: dict[str, Any]) -> tuple[str, str, bool]:
        """
        This function inserts the polygons chosen using the interactive
        tile-map into the `farmpolygons` table. This is only applicable
        to authenticated users.

        Args: (i) n_clicks - triggered by mouse click
              (ii) token - login access token
              (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        TABLE_NAME = "farmpolygons"
        try:

            if USE_LOCAL_DB:
                conn = db_connect()
                
                with conn.cursor() as cursor:
                    for row in stored_data:
                        row.setdefault("created_at", datetime.now().isoformat())

                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['%s'] * len(row))
                        values = tuple(row.values())

                        query = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
                        cursor.execute(query, values)

                    logger.info(f"Inserted {len(stored_data)} polygons successfully.")
                    return f"Inserted {len(stored_data)} polygons successfully.", "success", True

            else:
                client = get_supabase_client()
                # Add timestamp
                for item in stored_data:
                    item["created_at"] = datetime.now().isoformat()

                response = client.table(TABLE_NAME).insert(stored_data).execute()

                if response.data:
                    logger.info(f"Inserted {len(response.data)} polygons successfully.")
                    return f"Inserted {len(response.data)} polygons successfully.", "success", True
                else:
                    logger.error(f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}")
                    return f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}", "danger", True

        except Exception as e:
            logger.error(f"Error inserting polygons: {e}"), "danger", True