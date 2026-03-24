from typing import Any, Optional
from uuid import uuid4

from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate

def register(app):
    @app.callback(
        Output("clicked_point_store", "data"),
        Input("ndvi_plot", "clickData"),
        Input("ndmi_plot", "clickData"),
        State("geometry_map_store", "data"),
        prevent_initial_call=True,
    )
    def run(click_data_ndvi: Optional[dict], click_data_ndmi: Optional[dict], geometry_map: dict[str, str]) -> dict[str, Any]:
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

        click = click_data_ndvi if triggered == "ndvi_plot" else click_data_ndmi
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