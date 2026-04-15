import asyncio
import logging
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from aiohttp import ClientError
from celery.result import AsyncResult
from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
from plotly.graph_objects import Figure

from regen_queue.celery_app import celery_app
from regen_queue.tasks import fetch_timeseries
from utils.farm_stats import FarmDataProcessor, FarmStatsCalculator
from utils.isda_soil_data import main as get_soil_data
from utils.parse_contents import parse_contents

OutputType = tuple[
    Figure,
    Figure,
    dict[str, Any],
    dict[str, Any],
    Optional[str],
    list[dict[str, Any]],
    dict[str, Any],
]

def build_vi_figures(df: pd.DataFrame) -> tuple[go.Figure, go.Figure, dict[str, str]]:
    uuid_list = df["uuid"].unique()

    fig_ndvi = go.Figure()
    fig_ndmi = go.Figure()

    geometry_map = {row["uuid"]: row["geometry"] for _, row in df.iterrows()}

    for uuid in uuid_list:
        df_uuid = df[df["uuid"] == uuid]
        label = uuid[0:8]

        customdata = np.array([
            [row["uuid"], row["region"]]
            for _, row in df_uuid.iterrows()
        ])

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
                ),
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
                ),
            )
        )

    for fig, yaxis_title in ((fig_ndvi, "NDVI"), (fig_ndmi, "NDMI")):
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=yaxis_title,
            xaxis=dict(tickformat="%Y-%m-%d"),
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            margin=dict(l=20, r=20, t=30, b=20),
        )

    return fig_ndvi, fig_ndmi, geometry_map

def register(app):
    @app.callback(
        Output("vi_task_store", "data"),
        Output("vi_roi_store", "data"),
        Output("vi_task_poll", "disabled"),
        Output("vi_task_status", "children"),
        Input("upload_button", "n_clicks"),
        Input("upload-data", "contents"),
        Input("upload-data", "filename"),
        State("polygon_input", "value"),
        State("geometry_validation_check", "data"),
        prevent_initial_call=True
    )
    def enqueue_vi_task(
            n_clicks: int,
            file_contents: Optional[str],
            file_name: Optional[str],
            polygon_wkt: Optional[str],
            is_valid: bool
    ) -> tuple[dict[str, int], dict[str, Any], bool, str]:
        """
        Callback that enqueues time-series retrieval tasks to Celery.

        Args:
            n_clicks (int): clicks on the submit button
            file_contents (str, optional): file contents from uploaded .csv file
            file_name (str, optional): file name from uploaded .csv file
            polygon_wkt(str, optional): polygon in WKT format inputted on submission box
            is_valid (bool): check for WKT validity

        Returns:
            dict[str, int]: a dictionary containing task_id
            dict[str, Any]: input dataframe in dictionary format
            bool: task polling status
            str: task status information
        """
        trigger = ctx.triggered_id

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

        # Enqueue task to Celery app; can return task_id and status
        task = fetch_timeseries.delay(df_roi.to_dict("records"))

        return (
            {"task_id": task.id},
            df_roi.to_dict("records"),
            False,
            "Fetching NDVI and NDMI data..."
        )

    @app.callback(
        Output("vi_result_store", "data"),
        Output("vi_task_poll", "disabled", allow_duplicate=True),
        Output("vi_task_status", "children", allow_duplicate=True),
        Input("vi_task_poll", "n_intervals"),
        State("vi_task_store", "data"),
        prevent_initial_call=True,
    )
    def poll_vi_task(n_intervals, task_data) -> tuple[list[dict[str, Any]] | Any, bool, str]:
        """
        Callback for polling task status.

        Args:
            n_intervals (int): polling interval
            task_data (dict[str, Any]): input dataframe in dictionary format generated from data upload

        Returns:
            list[dict[str, Any]] | Any: update depending on polling status
            bool: polling status
            str: task status message
        """
        if not task_data:
            raise PreventUpdate

        # Poll task metadata
        result = AsyncResult(task_data["task_id"], app=celery_app)

        if result.state in {"PENDING", "RECEIVED", "STARTED", "RETRY"}:
            return no_update, False, f"Fetching vegetation and moisture data... {result.state.lower()}"

        if result.failed():
            return no_update, True, "Vegetation and moisture data failed to load."

        return result.result, True, "Vegetation and moisture data loaded."

    @app.callback(
        Output("ndvi_plot", "figure"),
        Output("ndmi_plot", "figure"),
        Output("farm_stats", "data"),
        Output("isda_soil_data", "data"),
        Output("polygon_wkt_store", "data"),
        Output("ndvi_timeseries", "data"),
        Output("geometry_map_store", "data"),
        Input("vi_result_store", "data"),
        State("vi_roi_store", "data"),
        prevent_initial_call=True,
    )
    def process_vi_result(df_records, roi_records) -> OutputType:
        """
        Callback that processes outputs after task completion.

        Args:
            df_records (dict[str, Any]): data generated from Celery task
            roi_records (dict[str, Any]): input data from user

        Returns:
            go.Figure: NDVI Plotly figure
            go.Figure: NDMI Plotly figure
            dict[str, Any]: farm statistics from the input data
            dict[str, Any]: ISDA soil data retrieved
            str: polygon WKT from polygon_wkt_store
            list[dict[str, Any]]: NDVI/NDMI data retrieved
            dict[str, Any]: UUID-geometry mapping
        """
        if not df_records or not roi_records:
            raise PreventUpdate

        df = pd.DataFrame(df_records)
        df_roi = pd.DataFrame(roi_records)

        fig_ndvi, fig_ndmi, geometry_map = build_vi_figures(df)

        preprocessor = FarmDataProcessor()
        farm_stats = FarmStatsCalculator(preprocessor)
        df_stats = farm_stats.calculate_stats(df)

        try:
            df_soil_data = asyncio.run(get_soil_data(df_roi))
        except ClientError as e:
            logging.exception("Failed to retrieve iSDA soil data")
            df_soil_data = []

        return (
            fig_ndvi,
            fig_ndmi,
            df_stats,
            df_soil_data,
            df_roi["geometry"].iloc[0],
            df.to_dict("records"),
            geometry_map,
        )