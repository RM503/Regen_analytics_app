import asyncio
import logging
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from aiohttp import ClientError
from celery.result import AsyncResult
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from plotly.graph_objects import Figure

from regen_queue.tasks import fetch_timeseries
from utils.farm_stats import FarmDataProcessor, FarmStatsCalculator
from utils.isda_soil_data import main as get_soil_data
from utils.parse_contents import parse_contents

OutputType = tuple[Figure, Figure, dict[str, Any], dict[str, Any], Optional[str], list[dict[str, Any]], dict[str, Any]]

def register(app):
    @app.callback(
        Output("ndvi_plot", "figure"),
        Output("ndmi_plot", "figure"),
        Output("farm_stats", "data"),  # Stored for use in separate callback
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
    def run(
            n_clicks: int,
            file_contents: Optional[str],
            file_name: Optional[str],
            polygon_wkt: Optional[str],
            is_valid: bool
    ) -> OutputType:
        """
        Depending on the validity check from the previous callback, the
        NDVI-NDMI time-series plots will be generated.

        Args: (i) n_clicks - the click that initiates the callback
              (ii) file_contents - the contents of the uploaded file
              (iii) file_name - the name of the uploaded file
              (iv) polygon_wkt - the polygon geometry in wkt notation
                                 if geometry entered through `upload` button
               (v) is_valid - geometry validation (from previous callback)

        Returns: (i) ndvi_plot - NDVI time-series plot
                 (ii) ndmi_plot - NDMI time-series plot
                 (iii) farm_stats - farmland stats in json
                 (iv) soil_stats - ISDA soil data in json
                 (v) polygon_store - polygon wkt
                 (vi) ndvi_timeseries - NDVI time-series data in dcc.Store
                 (vii) geometery_map_store - a dictionary mapping uuid to geometry wkt
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
            df_roi = pd.DataFrame({
                "uuid": [str(uuid4())],
                "region": [None],
                "area (acres)": [np.nan],
                "geometry": [polygon_wkt]
            })

        elif trigger == "upload-data":
            df_roi = parse_contents(file_contents, file_name)

        else:
            raise PreventUpdate

        df_records = fetch_timeseries.delay(df_roi.to_dict("records")).get(timeout=3600)
        df = pd.DataFrame(df_records)
        # Plot the data
        uuid_list = df["uuid"].unique()

        fig_ndvi = go.Figure()
        fig_ndmi = go.Figure()

        # create a mapping for uuid and corresponding geometry
        geometry_map = {row["uuid"]: row["geometry"] for _, row in df.iterrows()}
        for idx, uuid in enumerate(uuid_list):
            df_uuid = df[df["uuid"] == uuid]
            label = uuid[0:8]  # show only the first 8 characters of uuid on legend

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
        # df_stats = calculate_farm_stats(df)
        preprocessor = FarmDataProcessor()

        farm_stats = FarmStatsCalculator(preprocessor)
        df_stats = farm_stats.calculate_stats(df)

        # if iSDA API fails to return respose
        try:
            df_soil_data = asyncio.run(get_soil_data(df_roi))
        except ClientError as e:
            logging.warning(f"Failed to retrieve iSDA soil data: {e}")
            df_soil_data = []  # return an empty dataframe

        return (
            fig_ndvi,
            fig_ndmi,
            df_stats,
            df_soil_data,
            df_roi["geometry"].iloc[0],
            df.to_dict("records"),
            geometry_map
        )