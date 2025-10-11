# Dash app with callbacks for `Farmland Characteristics` page
import asyncio
from datetime import datetime
import logging
import re
from typing import Any, Optional
from uuid import uuid4

from aiohttp import ClientError
import dash
from dash import Dash, Input, Output, State, ctx, dash_table, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import ee
from flask import Flask
from flask import session
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import shapely
from shapely.geometry import Polygon

from auth.supabase_auth import get_supabase_client
from config import USE_LOCAL_DB, LOCAL_DB_CONFIG
from db.db_utils import db_connect
from .layout import layout
from .utils.vi_timeseries import combined_timeseries
from .utils.parse_contents import parse_contents
from .utils.farm_stats import calculate_farm_stats
from .utils.isda_soil_data import main as get_soil_data
from .utils.gee_images import get_rgb_image, convert_wkt_to_ee_geometry, get_image_dates

logger = logging.getLogger(__name__)

#dotenv.load_dotenv()

if USE_LOCAL_DB:
    logging.info(
        f"Running in LOCAL mode — connecting to PostgreSQL at "
        f"{LOCAL_DB_CONFIG['host']}:{LOCAL_DB_CONFIG['port']}, "
        f"database '{LOCAL_DB_CONFIG['database']}'."
    )
else:
    logging.info("Running in SUPABASE mode.")

def init_dash2(server: Flask) -> Dash:
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
        Output("polygon_wkt_store", "data"),
        Output("ndvi_timeseries", "data"),
        Output("geometry_map_store", "data"),
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
    ) -> tuple[Figure, Figure, dict[str, Any], dict[str, Any], str, list[dict[str, Any]]]:
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
                 (v) str - polygon wkt
        """
        trigger = ctx.triggered_id

        """
        The inputs are checked on whether they we submitted through the
        box or uploaded as a file. Regardless of choice, the `combined_timeseries()`
        function processes the time-series data and returns a dataframe.
        """
        if trigger == "upload_button":
            if not is_valid:
                raise PreventUpdate
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

        geometry_map = {row["uuid"]: row["geometry"] for _, row in df.iterrows()} # create a mapping for uuid and corresponding geometry
        for idx, uuid in enumerate(uuid_list):
            df_uuid = df[df["uuid"] == uuid]
            label = uuid[0:8] # show only the first 8 characters of uuid on legend
            
            customdata = np.array([[row["uuid"], row["region"]] for _, row in df_uuid.iterrows()])

            fig_ndvi.add_trace(
                go.Scatter(
                    x=df_uuid["date"], 
                    y=df_uuid["ndvi"], 
                    mode="lines+markers", 
                    name=label, 
                    connectgaps=True,
                    marker=dict(line=dict(color="black", width=1)),
                    customdata=customdata,
                    hovertemplate=(
                        "Date: %{x}<br>"
                        "NDVI: %{y}<br>"
                        "UUID: %{customdata[0]}<br>"
                        "Region: %{customdata[1]}<extra></extra>"
                    )
                )
            )

            fig_ndmi.add_trace(
                go.Scatter(
                    x=df_uuid["date"], 
                    y=df_uuid["ndmi"],
                    mode="lines+markers", 
                    name=label, 
                    connectgaps=True,
                    marker=dict(line=dict(color="black", width=1)),
                    customdata=customdata,
                    hovertemplate=(
                        "Date: %{x}<br>"
                        "NDMI: %{y}<br>"
                        "UUID: %{customdata[0]}<br>"
                        "Region: %{customdata[1]}<extra></extra>"
                    )
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

        return fig_ndvi, fig_ndmi, df_stats, df_soil_data, df_RoI["geometry"].iloc[0], df.to_dict("records"), geometry_map

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
            dbc.Alert("Soil data failed to be retrieved", color="danger")

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
        Output("clicked_point_store", "data"),
        Input("ndvi_plot", "clickData"),
        Input("ndmi_plot", "clickData"),
        State("geometry_map_store", "data"),
        prevent_initial_call=True,
    )
    def capture_click(clickData_ndvi: Optional[dict], clickData_ndmi: Optional[dict], geometry_map: dict[str, str]) -> dict[str, Any]:
        """
        This function retrieves data from `click events` occurring on the NDVI/NDMI plots
        to be used for generating Sentinel-2 raster images on specific dates.

        Args: (i) ndvi_plot - data from NDVI time-series plot
              (ii) ndmi_plot - data from NDMI time-series plot
              (iii) geometry_map_store - a dictionary mapping uuid to geometry wkt

        Returns: a dictionary-valued `click data` object stored in dcc.Store
        """
        triggered = ctx.triggered_id
        if triggered not in ["ndvi_plot", "ndmi_plot"]:
            raise PreventUpdate

        click = clickData_ndvi if triggered == "ndvi_plot" else clickData_ndmi
        if not click or "points" not in click or not click["points"]:
            raise PreventUpdate

        # Get click data
        point = click["points"][0]
        clicked_uuid = point["customdata"][0]
        clicked_date = str(point["x"]).split("T")[0]

        if clicked_uuid not in geometry_map:
            raise PreventUpdate

        clicked_wkt = geometry_map[clicked_uuid]

        return {
            "clicked_uuid": clicked_uuid,
            "clicked_wkt": clicked_wkt,
            "clicked_date": clicked_date,
            "nonce": str(uuid4()),  # optional, ensures the store updates every click
        }

    @app.callback(
        Output("image-modal", "is_open"),
        Output("gee-image", "src"),
        Input("clicked_point_store", "data"),
        Input("close-modal", "n_clicks"),
        State("image-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_image_modal(clicked_data: Optional[dict], close_clicks: Optional[int], is_open: bool) -> tuple[bool, str]:
        trigger_id = ctx.triggered_id

        # Close modal
        if trigger_id == "close-modal":
            return False, dash.no_update

        if not clicked_data or "clicked_wkt" not in clicked_data or "clicked_date" not in clicked_data:
            raise PreventUpdate

        clicked_wkt = clicked_data["clicked_wkt"]
        clicked_date = clicked_data["clicked_date"]

        # Convert WKT to EE geometry
        ee_geom = convert_wkt_to_ee_geometry(clicked_wkt)

        # Generate RGB image
        rgb_image = get_rgb_image(ee_geom, clicked_date)

        if rgb_image is None:
            return True, "" # No update

        # Generate thumbnail URL with dummy param to avoid caching
        vis_params = {
            "region": ee_geom.bounds().getInfo(),
            "scale": 10,
            "bands": ["B4", "B3", "B2"],
            "min": 0.0,
            "max": 0.3
        }
        
        image_url = rgb_image.getThumbURL(vis_params)

        return True, image_url

    # @app.callback(
    #     Output("date-slider", "marks"),
    #     Output("date-slider", "max"),
    #     Output("date-slider", "value"),
    #     Input("clicked_point_store", "data"),
    #     prevent_initial_call=True
    # )
    # def update_slider(clicked_data):
    #     if not clicked_data:
    #         raise PreventUpdate

    #     # Get dates for which image is available for provided geometry
    #     ee_geom = convert_wkt_to_ee_geometry(clicked_data["clicked_wkt"])
    #     start_date = clicked_data["clicked_date"]
    #     end_date = ee.Date(start_date).advance(30, "day")
    #     collection = (
    #         ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    #         .filterBounds(ee_geom)
    #         .filterDate(start_date, end_date)
    #         .sort("CLOUD_COVER")
    #     )
    #     unique_dates = get_image_dates(collection)

    #     slider_marks = {i: date for i, date in enumerate(unique_dates)}

    #     try:
    #         value_index = unique_dates.index(start_date)
    #     except ValueError:
    #         # pick closest date if exact one missing
    #         clicked_date = datetime.strptime(start_date, "%Y-%m-%d")
    #         available = [datetime.strptime(d, "%Y-%m-%d") for d in unique_dates]
    #         closest = min(available, key=lambda d: abs(d - clicked_date))
    #         value_index = available.index(closest)

    #     return slider_marks, len(unique_dates)-1, value_index


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

    # ========== Data INSERTs ==========
    """
    These are the tables that where data is directly inserted to when the INSERT
    button is clicked by an authenticated user. The will call trigger functions
    that will eventually update the other tables that appear in `farmland_statistics`
    dashboard.
    """
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
    def insert_soildata(n_clicks: int, token: str, stored_data: dict[str, Any]) -> tuple[str, str, bool]:
        """
        This function INSERTs the iSDA soil data to the `soildata` table in
        the Supabase database.

        Args: (i) n_clicks - triggered by mouse click
            (ii) token - login access token
            (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        TABLE_NAME = "soildata"
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
        } # USDA texture classification conversions

        try:
            if USE_LOCAL_DB:

                # ====== Local PostgreSQL mode ====== #

                conn = db_connect()
                with conn.cursor() as cursor:
                    dataset = stored_data

                    logging.info(f"Processing {TABLE_NAME}: {type(dataset)} -> {dataset[:2] if dataset else 'Empty'}")

                    if not isinstance(dataset[0], dict):
                        raise TypeError(f"Expected list of dicts for {TABLE_NAME}, got {type(dataset[0])}")

                    for row in dataset:
                        # Add a timestamp
                        row = {clean_column_name(k): v for k, v in row.items()} # Remove units from column names
                        row.setdefault("created_at", datetime.now().isoformat())

                        if not isinstance(row["texture_class"], int):
                            # Check if texture class is a string or integer
                            # DB stores it as integer
                            texture_class = row["texture_class"]
                            row["texture_class"] = texture_class_to_int[texture_class]

                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['%s'] * len(row))
                        values = tuple(row.values())

                        query = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
                        cursor.execute(query, values)

                return f"✅ {TABLE_NAME}: Inserted {len(dataset)} rows (Local DB).", "success", True
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

                response = client.table(TABLE_NAME).insert(dataset).execute()

                if response.data:
                    return f"Inserted {len(response.data)} polygons successfully.", "success", True
                else:
                    return f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}", "danger", True

        except Exception as e:
            logger.error(f"Error inserting polygons: {e}")
            return f"❌ Insert failed: {e}", "danger", True

    @app.callback(
        Output("insert_farm_stats_notification", "children"),
        Output("insert_farm_stats_notification", "color"),
        Output("insert_farm_stats_notification", "is_open"),
        Input("insert_farm_stats", "n_clicks"),
        State("token_store", "data"),
        State("farm_stats", "data"),
        prevent_initial_call=True
    )
    def insert_all_farm_stats(n_clicks: int, token: str, stored_data: list[dict[str, Any]]) -> tuple[str, str, bool]:
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
        TABLES = ["highndmidays", "peakvidistribution", "ndvipeaksperfarm"]

        messages = []

        try:

            if USE_LOCAL_DB:
                conn = db_connect()

                # ====== Local PostgreSQL mode ====== #

                with conn.cursor() as cursor:
                    for TABLE in TABLES:
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

                for TABLE in TABLES:
                    dataset = stored_data[f"df_{TABLE}"] # data corresponding to particular table
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

    return app
