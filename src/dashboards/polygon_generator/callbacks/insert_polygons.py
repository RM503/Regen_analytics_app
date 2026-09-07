from typing import Any

from dash import Input, Output, State

from db.db_client import get_db_runtime
from db.db_insert import local_db_insert_single, supabase_db_insert_single

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
    def run(n_clicks: int, token: str, stored_data: list[dict[str, Any]]) -> tuple[str, str, bool]:
        """
        This function inserts the polygons chosen using the interactive
        tile-map into the `farmpolygons` table. This is only applicable
        to authenticated users.

        Args: (i) n_clicks - triggered by mouse click
              (ii) token - login access token
              (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        table_name = "farmpolygons"
        insert = (
            local_db_insert_single
            if get_db_runtime().mode == "local"
            else supabase_db_insert_single
        )
        return insert(stored_data, table_name)
