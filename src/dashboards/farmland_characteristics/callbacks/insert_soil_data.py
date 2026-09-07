import re
from typing import Any

from dash import Input, Output, State

from db.db_client import get_db_runtime
from db.db_insert import local_db_insert_single, supabase_db_insert_single

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
    def insert_soildata(
        n_clicks: int,
        token: str,
        stored_data: list[dict[str, Any]],
    ) -> tuple[str, str, bool]:
        """
        This function inserts iSDA soil data into the `soildata` table in the
        configured database.

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

        dataset = []
        for item in stored_data:
            cleaned_item = {clean_column_name(key): value for key, value in item.items()}
            texture_class = cleaned_item.get("texture_class")
            if texture_class is not None and not isinstance(texture_class, int):
                cleaned_item["texture_class"] = texture_class_to_int[texture_class]
            dataset.append(cleaned_item)

        insert = (
            local_db_insert_single
            if get_db_runtime().mode == "local"
            else supabase_db_insert_single
        )
        return insert(dataset, table_name)
