from typing import Any
import json
from dash import Dash
import dash_bootstrap_components as dbc
from dash import Output, Input
import dash_leaflet as dl
import geopandas as gpd
from shapely.geometry import shape
from .layout import layout

app = Dash(__name__, requests_pathname_prefix="/dash1/", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Polygon generator"
app.layout = layout 

@app.callback(
    Output("map", "center"),
    Output("marker-layer", "children"),
    Input("location_dropdown", "value")
)
def toggle_map(location: str) -> tuple[list[float], list]:
    """
    This function controls map toggle from the location drop-down menu.
    The `Default` location refers to the centroid coordinates of Kenya.
    """
    location_w_coords = {
        "Default": [1.00, 38.00],
        "Laikipia_1": [0.2580, 36.5353],
        "Trans_Nzoia_1": [1.0199, 35.0211]
    }

    coords = location_w_coords.get(location, [1.00, 38.00])
    marker = dl.Marker(position=coords, children=dl.Popup(location or "Default")) # Marker placed at toggled location
    return coords, [marker]

@app.callback(
    Output("vector-layer", "data"),
    Input("location_dropdown", "value")
)   
def update_vector_layer(location: str) -> dict[str, Any]:
    """
    This function updates location toggles to associated vector layers.
    """
    # The `Default` location has no associated vector layer
    if location == "Default":
        return {"type": "FeatureCollection", "features": []}
    
    # Upload geometry file and check for correct CRS
    file_path = f"assets/{location}_results_aggregated.feather"
    gdf = gpd.read_feather(file_path, columns=["uuid", "area (acres)", "geometry"])
    if gdf.crs and gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    geojson_data = json.loads(gdf.to_json()) # Convert gdf to geojson

    # Include properties for tooltip features upon hovering
    for feature in geojson_data["features"]:
        props = feature["properties"]
        uuid = props.get("uuid", "N/A")
        area = props.get("area (acres)", "N/A")

        try:
            area_float = float(area)
            area_str = f"{area_float:.2f}"
        except (ValueError, TypeError):
            area_str = str(area)

        props["popup"] = f"UUID: {uuid}<br>Area: {area_str} acres"
    return geojson_data
    
@app.callback(
    Output("geojson-output", "children"),
    Output("polygon_count_alert", "is_open"),
    Output("polygon_count_alert", "children"),
    Input("edit_control", "geojson")
)
def update_output(geojson: dict) -> tuple[str, bool, str]:
    if geojson and "features" in geojson:
        wkt_list = []
        show_alert = False
        alert_message = ""

        for i, feature in enumerate(geojson["features"]):
            if i < 5:
                geom = feature.get("geometry")
                if geom:
                    try:
                        wkt = shape(geom).wkt
                        wkt_list.append(f"polygon {i+1}:\n{wkt}\n")
                    except Exception as e:
                        print(f"Error processing polygon {i+1}: {e}")
            else:
                show_alert = True
                alert_message = "⚠️ You can only draw up to 5 polygons."

        return "\n\n".join(wkt_list), show_alert, alert_message

    return "", True, "No polygons drawn yet."

if __name__ == "__main__":
    app.run(debug=True)