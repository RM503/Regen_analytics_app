from typing import Optional

from dash import Input, Output, State, dash, ctx
from dash.exceptions import PreventUpdate

from utils.gee_images import get_rgb_image, convert_wkt_to_ee_geometry

def register(app):
    @app.callback(
        Output("image-modal", "is_open"),
        Output("gee-image", "src"),
        Output("modal_title", "children"),
        Input("clicked_point_store", "data"),
        Input("close-modal", "n_clicks"),
        State("image-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_image_modal(clicked_data: Optional[dict], close_clicks: Optional[int], is_open: bool) -> tuple[
        bool, str, str]:
        """
        This function produces a popup containing GEE raster upon click events on
        the NDVI time-series points.
        """
        trigger_id = ctx.triggered_id

        # Close modal
        if trigger_id == "close-modal":
            return False, dash.no_update, dash.no_update

        if not clicked_data or "clicked_wkt" not in clicked_data or "clicked_date" not in clicked_data:
            raise PreventUpdate

        clicked_wkt = clicked_data["clicked_wkt"]
        clicked_date = clicked_data["clicked_date"]

        # Convert WKT to EE geometry
        ee_geom = convert_wkt_to_ee_geometry(clicked_wkt)

        # Generate RGB image
        rgb_image = get_rgb_image(ee_geom, clicked_date)

        if rgb_image is None:
            return True, "", "❌ No satellite image available for this date."

        # Generate thumbnail URL with dummy param to avoid caching
        vis_params = {
            "region": ee_geom.bounds().getInfo(),
            "scale": 10,
            "bands": ["B4", "B3", "B2"],
            "min": 0.0,
            "max": 0.4,
            "gamma": 1.3
        }

        image_url = rgb_image.getThumbURL(vis_params)
        modal_title = f"Satellite RGB Image on {clicked_date}"

        return True, image_url, modal_title