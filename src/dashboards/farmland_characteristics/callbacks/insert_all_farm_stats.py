from typing import Any

from dash import Input, Output, State

from db.db_client import get_db_runtime
from db.db_insert import local_db_insert_multi, supabase_db_insert_multi

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
    def run(
        n_clicks: int,
        token: str,
        stored_data: dict[str, list[dict[str, Any]]],
    ) -> tuple[str, str, bool]:
        """
        This function performs an INSERT of all the farm stat tables stored in
        the `farm_stats` dcc.Store. Depending on the configured database runtime,
        it inserts the data into local PostgreSQL or Supabase.

        Args: (i) n_clicks - triggered by mouse click
              (ii) token - login access token
              (iii) stored_data - list of datatables stored in dcc.Store

        Returns: Status message of the insert operation
        """

        # List of data tables stored in dcc.Store
        tables = ["highndmidays", "peakvidistribution", "ndvipeaksperfarm"]
        # The store uses display-oriented ``df_<table>`` keys, while the shared
        # insert functions intentionally accept actual database table names.
        datasets = {table: stored_data.get(f"df_{table}", []) for table in tables}
        insert = (
            local_db_insert_multi
            if get_db_runtime().mode == "local"
            else supabase_db_insert_multi
        )
        return insert(datasets, tables)
