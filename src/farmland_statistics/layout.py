from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from ..region_bboxes import region_bboxes_to_geojson, generate_location_w_coords

regions = region_bboxes_to_geojson()

# Tile map layers (not Sentinel-2 rasters)
esri_hybrid = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI"
)

esri_labels = dl.TileLayer(
    url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attribution="ESRI Labels"
)

region_bboxes = dl.GeoJSON(
    data=regions,
    id="region_bboxes",
    zoomToBounds=True,
    options=dict(style=dict(weight=1.5, color="cyan", fillOpacity=0))
)

location_w_coords = generate_location_w_coords(regions)

map_indicators = [
    "ndmi_max",
    "bulk_density",
    "calcium_extractable",
    "carbon_organic",
    "carbon_total",
    "clay_content",
    "iron_extractable",
    "magnesium_extractable",
    "nitrogen_total",
    "ph",
    "phosphorous_extractable",
    "potassium_extractable",
    "sand_content",
    "silt_content",
    "stone_content",
    "sulphur_extractable",
    "texture_class",
    "zinc_extractable"
]

layout = dbc.Container([
    dbc.Row([
        html.H1("Farmland Statistics", style={"fontSize": "30px", "textAlign": "center"}),
        html.Div([
            html.P("Select options from the dropdown menus below:"),
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
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
                        dbc.Col([
                            dcc.Dropdown(
                                options=map_indicators,
                                value="ndmi_max",
                                id="indicator-dropdown",
                                style={
                                        "width": "200px",
                                        "backgroundColor": "#222",   # background of the dropdown
                                        "color": "black",            # selected text color
                                        "border": "1px solid #444",
                                    },
                                clearable=True
                            )
                        ])
                    ])
                ])
            ])
        ]),
        html.Hr()
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="choropleth_map")
        ], xs=6, md=6, lg=6),
        dbc.Col([
            dcc.Graph(id="high_ndmi")
        ], xs=6, md=6, lg=6)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="ndvi_peak_monthly")
        ], xs=4, md=4, lg=4),
        dbc.Col([
            dcc.Graph(id="ndvi_peak_annual")
        ], xs=4, md=4, lg=4),
        dbc.Col([
            dcc.Graph(id="moisture_level")
        ], xs=4, md=4, lg=4)
    ]),
], fluid=True, className="px-2 px-md-4 px-lg-5")