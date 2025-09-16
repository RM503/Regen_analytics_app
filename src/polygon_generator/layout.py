# Dashboard 1 layout
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import geopandas as gpd 
import json

from .utils import generate_location_w_coords

# Import administrative boundaries shapefile and convert to geojson
gdf = gpd.read_file("src/polygon_generator/shapefiles/ken_adm_iebc_20191031_shp/ken_admbnda_adm2_iebc_20191031.shp")
if gdf.crs and gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

geometries = json.loads(gdf["geometry"].to_json())

with open("src/polygon_generator/region_bboxes.geojson", "r") as f:
    regions = json.load(f)

# Tile map layers (not Sentinel-2 rasters)
esri_hybrid = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI",
    id="ESRI_Satellite"
)

esri_labels = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI Labels",
    id="ESRI_Labels"
)

admin_boundaries = dl.GeoJSON(
    data=geometries,
    id="admin_boundaries",
    options=dict(style=dict(weight=1.5, color="red", fillOpacity=0))
)

region_bboxes = dl.GeoJSON(
    data=regions,
    id="region_bboxes",
    zoomToBounds=True,
    options=dict(style=dict(weight=1.5, color="blue", fillOpacity=0))
)

edit_control = dl.EditControl(
    id="edit_control", 
    draw={"rectangle": True, "polygon": True, "marker": True, "circle": False, "polyline": False, "circlemarker": False}
)

# Distributor locations with coordinates go here
location_w_coords = generate_location_w_coords()

# Layout - map, data panel and alerts
layout = dbc.Container([
    # Hidden div to store the access token for callbacks
    html.Div(id="token-store", style={"display": "none"}),
    dbc.Row([
        html.H1("Polygon generator", style={"fontSize": "30px", "textAlign": "center"})
    ]),
    dbc.Row([
        html.P("Use the dropdown menu and interactive map to toggle to various distributor locations and draw polygons. At any given time," \
        " the maximum number of polygons drawn should be kept to five. Use the coordinates of the polygons displayed for further querying purposes. \
        Note that the 'Default' location does not refer to any specific area of interest and is merely a placeholder.")
    ]),
    dbc.Row([
        dbc.Col([
            dl.Map(
                id="map",
                children=[
                    esri_hybrid, esri_labels, admin_boundaries, region_bboxes, dl.FeatureGroup([edit_control]), dl.LayerGroup(id="marker-layer"),
                    dl.GeoJSON(
                        id="vector-layer", 
                        zoomToBounds=True, 
                        options=dict(
                            style=dict(weight=2, color="blue", fillOpacity=0.4),
                            hoverStyle=dict(weight=4, color="red", fillOpacity=0.7),
                        ),
                        zoomToBoundsOnClick=True
                    )
                ],
                center=location_w_coords["Default"],
                zoom=7,
                style={"height": "85vh"}
            ),
        ], xs=6),
        dbc.Col([
            html.Div(
                [
                    html.Label("Latitude/Longitude box: ", style={"marginRight": "10px"}),
                    dcc.Input(
                        id="coordinate_input_box",
                        type="text",
                        placeholder="Enter latitude, longitude",
                        n_submit=0,
                        style={
                            "width": "725px",
                            "backgroundColor": "#222",   
                            "color": "white",            
                            "border": "1px solid #444",
                        }
                    )
                ]
            ),
            html.Div([
                html.Label("Region dropdown"),
                dcc.Dropdown(
                    options=list(location_w_coords.keys()),
                    value="Default",
                    id="location_dropdown",
                    style={
                        "backgroundColor": "#222",   
                        "color": "black",            
                        "border": "1px solid #444",
                    },
                    clearable=True
                )
            ]),
            html.Pre(
                id="geojson-output", 
                style={
                    "whiteSpace": "pre-wrap", 
                    "wordBreak": "break-word",
                    "height": "500px", 
                    "overflow": "auto",
                    "border": "1px solid #ccc", 
                    "padding": "10px"
                }
            ),
            html.Div([
                dbc.Button("Download polygons", id="download_button", n_clicks=0, disabled=True),
                dcc.Download(id="download_polygons"), 
                dcc.Interval(id="token_interval", interval=500, max_intervals=1),
                dcc.Store(id="token_store", storage_type="session"),
                dbc.Button("INSERT", id="insert_button", disabled=True),
                dcc.Store(id="polygons_store"), # Stores data on selected polygons
            ], style={"display": "flex", "gap": "10px"}),
            dbc.Alert(id="polygon_count_alert", is_open=False, color="warning", duration=10000),
            dbc.Alert(id="area_limit_alert", is_open=False, color="danger", duration=10000),
            dbc.Alert(id="insert_notification", is_open=False, className="mb-2", duration=10000)
        ], xs=6)
    ])
], fluid=True)
