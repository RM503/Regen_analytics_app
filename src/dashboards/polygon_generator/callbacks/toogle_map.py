import logging

import dash_leaflet as dl

from dash import Input, Output, State 

from utils.region_bboxes import generate_location_w_coords, region_bboxes_to_geojson

logger = logging.getLogger(__name__)

regions = region_bboxes_to_geojson()

def register(app):
    @app.callback(
        Output("map", "center"),
        Output("marker-layer", "children"),
        Input("location_dropdown", "value"),
        Input("coordinate_input_box", "n_submit"),
        State("coordinate_input_box", "value"),
        prevent_initial_call=True
    )
    def run(location: str | None, n_submit: int | None, coords: str | None) -> tuple[list[float], list]:
        """ 
        This callback toggles the map based on user input (dropdown or coordinate box).
        Defaults to (38.00, 1.00)
        """
        # Fallback to default coordinates 
        location_w_coords = generate_location_w_coords(regions)
        default_coords = [38.00, 1.00]
        loc_coords = location_w_coords.get(location, default_coords)
        loc_marker = dl.Marker(position=loc_coords, children=dl.Popup(location or "Default"))

        if n_submit and coords:
            try:
                lat_str, lon_str = [x.strip() for x in coords.split(",")]
                lat, lon = float(lat_str), float(lon_str)

                marker = dl.Marker(
                    position=[lat, lon],
                    children=dl.Popup(f"{lat:.6f}, {lon:.6f}")
                )
                return [lat, lon], [marker]

            except Exception as e:
                logging.error(f"Error parsing coordinates '{coords}': {e}")

        return loc_coords, [loc_marker]