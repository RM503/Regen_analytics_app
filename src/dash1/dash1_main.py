# Dashboard 1 main file (callbacks and etc.)
from uuid import uuid4
from typing import Any
import json
import dash
from dash import (
    Dash, 
    dash_table,
    dcc,
    Input,
    Output,
    State
)
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from .layout import layout

app = Dash(__name__, requests_pathname_prefix="/dash1/", external_stylesheets=[dbc.themes.BOOTSTRAP])
#app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Polygon generator"
app.layout = layout 

# Callbacks

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
    file_path = f"src/dash1/assets/{location}_results_aggregated.feather"
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

        props["popup"] = f"uuid: {uuid}<br>Area: {area_str} acres"
    return geojson_data
    
@app.callback(
    Output("geojson-output", "children"),
    Output("polygon_count_alert", "is_open"),
    Output("polygon_count_alert", "children"),
    Output("polygons_store", "data"),
    Input("edit_control", "geojson")
)
def update_output(geojson: dict) -> tuple[str | dict[str, Any], bool, str, str | dict[str, Any]]:
    """
    This function displays the geometries polygons drawn on
    the map, with a maximum of five polygons allowed.
    """
    if geojson and "features" in geojson:
        wkt_list = []
        polygon_dict = {
            "uuid": [],
            "area (acres)": [],
            "geometry": []
        }
        show_alert = False
        alert_message = ""

        for i, feature in enumerate(geojson["features"]):
            if i < 5:
                geom = feature.get("geometry")
                if geom:
                    try:
                        wkt = shape(geom).wkt
                        area = shape(geom).area * (111_000**2) * 0.000247105 # area in acres (rough conversion to physical distance)
                        wkt_list.append(f"polygon {i+1}:\n{wkt}\n")

                        # Append to polygon_dict
                        polygon_dict["uuid"].append(str(uuid4()))
                        polygon_dict["area (acres)"].append(area)
                        polygon_dict["geometry"].append(wkt)
                    except Exception as e:
                        print(f"Error processing polygon {i+1}: {e}")
            else:
                show_alert = True
                alert_message = "⚠️ You can only draw up to 5 polygons."
        
        polygon_df = pd.DataFrame(polygon_dict)
        polygon_table = dash_table.DataTable(
            data=polygon_df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in polygon_dict.keys()],
        )

        return polygon_table, show_alert, alert_message, polygon_df.to_dict("records")

    return "", True, "No polygons drawn yet.", ""

@app.callback(
    Output("download_polygons", "data"),
    Input("download_button", "n_clicks"),
    State("polygons_store", "data"),
    prevent_initial_call=True
)
def download_polygons(n_clicks: int, stored_data: dict[str, Any]) -> Any:
    if stored_data:
        df = pd.DataFrame(stored_data)
        return dcc.send_data_frame(df.to_csv, "polygons.csv", index=False)
    return dash.no_update

if __name__ == "__main__":
    app.run(debug=True)