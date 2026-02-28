# Dashboard app with callbacks for `Polygon Generator` page

import logging
from typing import Any

import dash
from dash import Dash, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from flask import Flask
from flask import session
import pandas as pd

from .callbacks import (
    insert_polygons,
    toogle_map, 
    update_output, 
    update_vector_layer
)
from .layout import layout

logger = logging.getLogger(__name__)


def init_dash1(server: Flask) -> Dash:
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/polygon_generator/", 
        external_stylesheets=[dbc.themes.DARKLY],
    )

    app.title = "Polygon Generator"
    app.layout = layout

    # Registered callbacks
    insert_polygons.register(app)
    toogle_map.register(app)
    update_output.register(app)
    update_vector_layer.register(app)

    @app.callback(
        Output("download_button", "disabled"),
        Input("polygons_store", "data")
    )
    def enable_download_button(stored_data: dict[str, Any]) -> bool:
        # Enables download button only when selected polygon data are displayed
        if not stored_data:
            return True
        
        return False
    
    @app.callback(
        Output("download_polygons", "data"),
        Input("download_button", "n_clicks"),
        State("polygons_store", "data"),
        prevent_initial_call=True
    )
    def download_polygons(n_clicks: int, stored_data: dict[str, Any]) -> Any:
        if stored_data:
            df = pd.DataFrame(stored_data)
            df.rename(columns={"area": "area (acres)"}, inplace=True)
            return dcc.send_data_frame(df.to_csv, "polygons.csv", index=False)
        return dash.no_update
    
    @app.callback(
        Output("token_store", "data"),
        Input("token_interval", "n_intervals")
    )
    def store_token(_) -> str | None:
        # Stores access token to dcc.Store in layout
        token = session.get("access_token")

        return token
    
    @app.callback(
        Output("insert_button", "disabled"),
        Input("token_store", "data"),
        Input("polygons_store", "data"),
    )
    def enable_insert_button(token: str, stored_data: dict[str, Any]) -> bool:
        """
        This function enables the INSERT button only when the user
        is authenticated and authenticated user selects polygons.
        """
        # Condition 1: user not authenticated
        if not token:
            return True  # disabled

        # Condition 2: authenticated but no polygons yet
        if not stored_data:
            return True  # disabled

        # Both conditions met
        return False  
    
    return app