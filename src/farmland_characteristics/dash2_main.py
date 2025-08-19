# Dash app with callbacks for `Farmland Characteristics` page
import datetime as datetime
from typing import Any, Optional
from uuid import uuid4
import asyncio
import numpy as np
import pandas as pd
from dash import Dash, Input, Output, State, ctx, dash_table 
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import session
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import shapely
from shapely.geometry import Polygon
from .layout import layout
from auth.supabase_auth import get_supabase_client
from src.farmland_characteristics.utils.vi_timeseries import combined_timeseries
from src.farmland_characteristics.utils.parse_contents import parse_contents
from src.farmland_characteristics.utils.farm_stats import calculate_farm_stats
from src.farmland_characteristics.utils.isda_soil_data import main as get_soil_data
from aiohttp import ClientError
import logging 

logger = logging.getLogger(__name__)

def init_dash2(server):
    app = Dash(
        __name__, 
        server=server,
        routes_pathname_prefix="/farmland_characteristics/", 
        external_stylesheets=[dbc.themes.DARKLY]
    )
    app.title = "Farmland Characteristics"
    app.layout = layout 

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
        Output("ndvi_plot", "figure"),
        Output("ndmi_plot", "figure"),
        Output("farm_stats", "data"), # Stored for use in separate callback
        Output("isda_soil_data", "data"),
        Input("upload_button", "n_clicks"),
        Input("upload-data", "contents"),
        Input("upload-data", "filename"),
        State("polygon_input", "value"),
        State("geometry_validation_check", "data"),
        prevent_initial_call=True
    )
    def plot_vi_data(
        n_clicks: int, 
        file_contents: Optional[str], 
        file_name: Optional[str], 
        polygon_wkt: Optional[str], 
        is_valid: bool
    ) -> tuple[Figure, Figure, dict[str, Any], dict[str, Any]]:
        """
        Depending on the validity check from the previous callback, the
        NDVI-NDMI time-series plots will be generated.

        Args: (i) n_clicks - the click that initiates the callback
            (ii) file_contents - the contents of the uploaded file
            (iii) file_name - the name of the uploaded file
            (iv) polygon_wkt - the polygon geometry in wkt notation
                if geometry entered through `upload` button
            (v) is_valid - geometry validation (from previous callback)

        Returns: (i) Figure - NDVI time-series plot
                (ii) Figure - NDMI time-series plot
                (iii) dict - farmland stats in json
                (iv) dict - ISDA soil data in json
        """
        trigger = ctx.triggered_id
        
        """
        The inputs are checked on whether they we submitted through the
        box or uploaded as a file. Regardless of choice, the `combined_timeseries()`
        function processes the time-series data and returns a dataframe.
        """
        if trigger == "upload_button":
            if not is_valid:
                PreventUpdate
            df_RoI = pd.DataFrame({
                "uuid": [str(uuid4())],
                "region": [None],
                "area (acres)": [np.nan],
                "geometry": [polygon_wkt]
            })
            df = combined_timeseries(df_RoI)

        elif trigger == "upload-data":
            df_RoI = parse_contents(file_contents, file_name)
            df = combined_timeseries(df_RoI)

        else:
            raise PreventUpdate

        # Plot the data
        uuid_list = df["uuid"].unique()

        fig_ndvi = go.Figure()
        fig_ndmi = go.Figure()
        
        for idx, uuid in enumerate(uuid_list):
            df_uuid = df[df["uuid"] == uuid]
            label = uuid[0:8] # show only the first 8 characters of uuid on legend

            fig_ndvi.add_trace(
                go.Scatter(
                    x=df_uuid["date"], y=df_uuid["ndvi"], mode="lines+markers", name=label, connectgaps=True,
                    marker=dict(line=dict(color="black", width=1))
                )
            )

            fig_ndmi.add_trace(
                go.Scatter(
                    x=df_uuid["date"], y=df_uuid["ndmi"], mode="lines+markers", name=label, connectgaps=True,
                    marker=dict(line=dict(color="black", width=1))
                )
            )
        fig_ndvi.update_layout(
            xaxis_title="Date",
            yaxis_title="NDVI",
            xaxis=dict(tickformat="%Y-%m-%d"),
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_ndmi.update_layout(
            xaxis_title="Date",
            yaxis_title="NDMI",
            xaxis=dict(tickformat="%Y-%m-%d"),
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        # Calculate farmland stats and retrieve iSDA soil data
        df_stats = calculate_farm_stats(df)

        # if iSDA API fails to return respose
        try:
            df_soil_data = asyncio.run(get_soil_data(df_RoI))
        except ClientError as e:
            logging.warning(f"Failed to retrieve iSDA soil data: {e}")
            df_soil_data = [] # return an empty dataframe

        return fig_ndvi, fig_ndmi, df_stats, df_soil_data

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
    def display_soil_data(df_soil: dict[str, Any]):
        """
        This function displays the isDA soil data
        as a Dash data table.

        Args: df_stats - the iSDA soil data json

        Returns: iSDA soil Dash data table
        """
        if not df_soil:
            dbc.Alert("Soil data failed to be retrieved", color="danger")
        
        return dash_table.DataTable(
            data=df_soil,
            columns=[{"name": col, "id": col} for col in df_soil[0].keys()],
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
        Output("insert_button", "disabled"),
        Input("token_store", "data"),
        Input("farm_stats", "data"),
        Input("isda_soil_data", "data")
    )
    def enable_insert_button(
        token: str,
        farm_stats: dict[str, Any], 
        isda_soil_data: dict[str, Any]
    ) -> bool:

        if not token:
            return True
        if not farm_stats or not isda_soil_data:
            return True
        return False
    
    # ========== Data INSERTs ==========
    """
    These are the tables that where data is directly inserted to when the INSERT
    button is clicked by an authenticated user. The will call trigger functions
    that will eventually update the other tables that appear in `farmland_statistics`
    dashboard.
    """

    def insert_soildata(n_clicks: int, token: str, stored_data: dict[str, Any]) -> tuple[str, bool]:
        """
        This function INSERTs the iSDA soil data to the `soildata` table in
        the Supabase database.

        Args: (i) n_clicks - triggered by mouse click
            (ii) token - login access token
            (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        TABLE_NAME = "soildata"

        try:
            client = get_supabase_client()

            # Add timestamp 
            for item in stored_data:
                item["created_at"] = datetime.now().isoformat()

            response = client.table(TABLE_NAME).insert(stored_data).execute()

            if response.data:
                return f"Inserted {len(response.data)} polygons successfully.", True
            else:
                return f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}", True

        except Exception as e:
            logger.error(f"Error inserting polygons: {e}"), True

    @app.callback(
        Input("insert_button", "n_clicks"),
        State("token_store", "data"), 
        State("farm_stats", "data"),
        prevent_initial_call=True
    )
    def insert_all_farm_stats(n_clicks: int, token: str, stored_data: dict[str, Any]) -> tuple[str, bool]:
        """
        This function performs an INSERT of all the farm stat tables stored in
        the `farm_stats` dcc.Store.
        """

        # List of data tables stored in dcc.Store
        TABLES = ["highndmidays", "peakvidistribution", "soildata"]

        client = get_supabase_client()
        messages = []

        try:
            for TABLE in TABLES:
                dataset = stored_data[TABLE] # data corresponding to particular table
                if dataset:
                    response = client.table(TABLE).insert(dataset).execute()

                    if response.data:
                        messages.append(f"✅ {TABLE}: Inserted {len(response.data)} rows.")
                    else:
                        messages.append(
                            f"❌ {TABLE}: Insert failed ({getattr(response, 'error', 'Unknown error')})."
                        )

            return " | ".join(messages) if messages else "⚠️ No data to insert."

        except Exception as e:
            logger.error(f"Insert error: {e}")
            return f"❌ Error inserting data: {e}"

    return app