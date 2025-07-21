from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl

# Tile map layers (not Sentinel-2 rasters)
esri_hybrid = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI"
)

esri_labels = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI Labels"
)

location_w_coords = {
        "Laikipia_1": [0.2580, 36.5353],
        "Trans_Nzoia_1": [1.0199, 35.0211]
    }

layout = dbc.Container([
    dbc.Row([
        html.H1("Farmland analytics", style={"fontSize": "30px", "textAlign": "center"}),
        html.Div([
            html.P("Select a region from the dropdown below:"),
            dcc.Dropdown(
                options=list(location_w_coords.keys()),
                value="Trans_Nzoia_1",
                id="location-dropdown",
                style={
                        "width": "200px",
                        "backgroundColor": "#222",   # background of the dropdown
                        "color": "black",            # selected text color
                        "border": "1px solid #444",
                    },
                clearable=True
            )
        ]),
        html.Hr()
    ]),
    dbc.Row([
        dbc.Col([
            dl.Map(
                id="map",
                children=[
                    esri_hybrid, esri_labels
                ],
                center=location_w_coords["Trans_Nzoia_1"],
                zoom=12,
                style={"height": "50vh"}
            )
        ], xs=6),
        dbc.Col([
            dcc.Graph(id="high_ndmi")
        ])
    ])
])