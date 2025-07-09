from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl

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

location_w_coords = {
        "Default": [1.00, 38.00],
        "Laikipia_1": [0.2580, 36.5353],
        "Trans_Nzoia_1": [1.0199, 35.0211]
    }

layout = dbc.Container([
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
                    esri_hybrid, esri_labels, dl.FeatureGroup([edit_control]), dl.LayerGroup(id="marker-layer"),
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
            html.Div([
                dcc.Dropdown(
                    options=list(location_w_coords.keys()),
                    value="Default",
                    id="location_dropdown"
                )
            ]),
            html.Pre(id="geojson-output", style={
                "whiteSpace": "pre-wrap", "wordBreak": "break-word",
                "height": "75vh", "overflow": "auto",
                "border": "1px solid #ccc", "padding": "10px"
            }),
            html.Div([
                html.Button("Download polygons", id="download_button", n_clicks=0),
                dcc.Download(id="download_polygons"), 
                dcc.Store(id="polygons_store")
            ]),
            dbc.Alert(id="polygon_count_alert", is_open=False, color="warning")
        ], xs=6)
    ])
], fluid=True)
