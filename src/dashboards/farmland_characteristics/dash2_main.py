# Dash app with callbacks for `Farmland Characteristics` page
import logging
from typing import Any

import dash
from dash import Dash, Input, Output, State, dash_table, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import Flask
from flask import session
import pandas as pd
import shapely
from shapely.geometry import Polygon

from .callbacks import (
    capture_click,
    insert_all_farm_stats,
    insert_soil_data,
    plot_vi_data,
    toggle_image_modal
)
from .layout import layout

logger = logging.getLogger(__name__)

#dotenv.load_dotenv()

def init_dash2(server: Flask) -> Dash:
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/farmland_characteristics/",
        external_stylesheets=[dbc.themes.DARKLY]
    )
    app.title = "Farmland Characteristics"
    app.layout = layout

    # Registered callbacks
    capture_click.register(app)
    insert_all_farm_stats.register(app)
    insert_soil_data.register(app)
    plot_vi_data.register(app)
    toggle_image_modal.register(app)

    @app.callback(
        Output("invalid_geometry_alert", "is_open"),
        Output("invalid_geometry_alert", "children"),
        Output("geometry_validation_check", "data"),
        Input("upload_button", "n_clicks"),
        State("polygon_input", "value"),
        prevent_initial_call=True
    )
    def validate_input(n_clicks: int, polygon_wkt: str) -> tuple[bool, str, bool]:
        """
        This function is used to validate the type of geometry that can be typed
        into the submission box. It will throw an error if object is anything
        but a POLYGON geometry (even MULTIPOLYGON geometries).

        Args: (i) n_clicks - the click that initiates the callback
              (ii) polygon_wkt - the polygon geometry in wkt notation

        Returns: the return values depend on whether an improper polygon format has been
                entered.
        """
        try:
            geom = shapely.wkt.loads(polygon_wkt)

            # Check instance type
            if isinstance(geom, Polygon):
                return False, "", True
            else:
                return True, f"❌ Input is not a single POLYGON. Detected: {type(geom).__name__}", False

        except Exception as e:
            return True, f"❌ Invalid WKT format: {str(e)}", False

    @app.callback(
        Output("farm_stats_container", "children"),
        Input("farm_stats", "data")
    )
    def display_farm_stats(farm_stats: dict[str, Any]):
        """
        This function displays the farmland statistics data
        as a Dash data table.

        Args: df_stats - the farmland statistics data json

        Returns: farmland statistics Dash data table
        """
        if not farm_stats or "df_stats" not in farm_stats:
            # farm_stats is None, empty, or missing expected keys
            raise PreventUpdate

        df_stats = farm_stats["df_stats"]

        if not df_stats:
            raise PreventUpdate

        return dash_table.DataTable(
            data=df_stats,
            columns=[{"name": col, "id": col} for col in df_stats[0].keys()],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"},
            style_header={"backgroundColor": "#111", "color": "white"},
            style_data={"backgroundColor": "#222", "color": "white"},
        )

    @app.callback(
        Output("isda_soil_data_container", "children"),
        Input("isda_soil_data", "data"),
        prevent_initial_call=True
    )
    def display_soil_data(df_soildata: dict[str, Any]):
        """
        This function displays the isDA soil data
        as a Dash data table.

        Args: df_stats - the iSDA soil data json

        Returns: iSDA soil Dash data table
        """
        if not df_soildata:
            return dbc.Alert("Soil data failed to be retrieved", color="danger")

        return dash_table.DataTable(
            data=df_soildata,
            columns=[{"name": col, "id": col} for col in df_soildata[0].keys()],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': '#111', 'color': 'white'},
            style_data={'backgroundColor': '#222', 'color': 'white'},
        )

    @app.callback(
        Output("token_store", "data"),
        Input("token_interval", "n_intervals")
    )
    def store_token(_) -> str | None:
        # Stores access token to dcc.Store in layout
        token = session.get("access_token")

        return token

    @app.callback(
        Output("insert_soil_data", "disabled"),
        Output("insert_farm_stats", "disabled"),
        Input("token_store", "data"),
        Input("farm_stats", "data"),
        Input("isda_soil_data", "data")
    )
    def enable_insert_button(token, farm_stats, isda_soil_data):
        soil_disabled = not token or not isda_soil_data
        farm_disabled = not token or not farm_stats
        return soil_disabled, farm_disabled

    @app.callback(
        Output("download_soil_data_button", "disabled"),
        Input("isda_soil_data", "data")
    )
    def enable_soil_data_download(stored_data: dict[str, Any]) -> bool:
        if not stored_data:
            return True 
        return False
    
    @app.callback(
        Output("download_farm_stats_button", "disabled"),
        Input("farm_stats", "data")
    )
    def enable_farm_stats_download(stored_data: dict[str, Any]) -> bool:
        if not stored_data:
            return True 
        return False

    @app.callback(
        Output("download_soil_data", "data"),
        Input("download_soil_data_button", "n_clicks"),
        State("isda_soil_data", "data"),
        prevent_initial_call=True
    )
    def download_soil_data(n_clicks: int, stored_data: dict[str, Any]) -> Any:
        # Enables downloading of soildata
        if stored_data:
            df = pd.DataFrame(stored_data)
            return dcc.send_data_frame(df.to_csv, "soil_data.csv", index=False)
        return dash.no_update
    
    @app.callback(
        Output("download_farm_stats", "data"),
        Input("download_farm_stats_button", "n_clicks"),
        State("farm_stats", "data"),
        prevent_initial_call=True
    )
    def download_farm_stats(n_clicks: int, stored_data: dict[str, Any]) -> Any:
        # Enables downloading of farm stats
        if stored_data:
            df = pd.DataFrame(stored_data["df_stats"])
            return dcc.send_data_frame(df.to_csv, "farm_stats.csv", index=False)
        return dash.no_update

    return app
