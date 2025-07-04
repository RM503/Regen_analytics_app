import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import html

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

edit_control = dl.EditControl(
    id="edit_control", 
    draw={"rectangle": True, "polygon": True, "marker": True, "circle": False, "polyline": False, "circlemarker": False}
)

layout = dbc.Container([
    dbc.Row([
        html.H1("Sentinel-2 VI time-series generator", style={"fontSize": "30px", "textAlign": "center"})
    ]),
    dbc.Row([
        dbc.Col([
            dl.Map(
                children=[esri_hybrid, esri_labels, dl.FeatureGroup([edit_control])],
                center=[1.00, 38.00],
                zoom=7,
                style={"height": "90vh"}
            )
        ], xs=6),
        dbc.Col([
            html.Pre(id="geojson-output", style={
                "whiteSpace": "pre-wrap", "wordBreak": "break-word",
                "height": "90vh", "overflow": "auto",
                "border": "1px solid #ccc", "padding": "10px"
            }),
            dbc.Alert(id="polygon_count_alert", is_open=False, color="warning")
        ], xs=6)
    ])
], fluid=True)