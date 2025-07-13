from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import logging 

logger = logging.getLogger(__name__)

# Define blank canvas on which NDVI/NDMI time-seres are generated

fig_ndvi = go.Figure()
fig_ndvi.update_layout(
    width=650,
    height=300,
    plot_bgcolor="#222",      
    paper_bgcolor="#222",     
    font=dict(color="white"), 
    xaxis_title="Date",
    xaxis=dict(range=[datetime(2020, 1, 1), datetime(2024, 12, 31)], type="date"),
    yaxis_title="NDVI",
    yaxis=dict(range=[-0.5, 1]),
    margin=dict(l=20, r=20, t=30, b=20)
)

fig_ndmi = go.Figure()
fig_ndmi.update_layout(
    width=650,
    height=300,
    plot_bgcolor="#222",      
    paper_bgcolor="#222",     
    font=dict(color="white"), 
    xaxis_title="Date",
    xaxis=dict(range=[datetime(2020, 1, 1), datetime(2024, 12, 31)], type="date"),
    yaxis_title="NDMI",
    yaxis=dict(range=[-0.5, 1]),
    margin=dict(l=20, r=20, t=30, b=20)
)

layout = dbc.Container([
    dcc.Store(id="geometry_validation_check"),
    dbc.Row([
        html.H1("Farmland vegetation and moisture", style={"fontSize": "30px", "textAlign": "center"})
    ]),
    dbc.Row([
        html.P("Use the polygon data generated from the 'Polygon Generator' app to obtain NDVI and NDMI time-series curves \
               of the queried region(s). Polygon data can be either typed individually or uploaded. The plots will display \
               a maximum of five curves per category.")
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("Definitions"), 
            html.P("In remote-sensing, the 'Normalized Difference Vegetation Index' (NDVI) is a simple, yet powerful, indicator \
                   used to assess 'greenness' of regions. As a result, it can be used to infer vegetation health, crop cycles etc.\
                   It has a range between -1 and +1, with higher positive values indicating vegetation."),
            html.P("Similarly, the 'Normalized Difference Moisture Index' (NDMI) is used to assess the amount of moisture \
                   available in the plants and surrounding soil and can be an indicator of whether or not a farm is being irrigated."),
            html.Br(),
            html.H4("Add polygon data"),
            html.P("Type polygon data in the box (one per submission)"),
            dcc.Textarea(
                id="polygon_input",
                value="Add polygon geometry here",
                style={"width": "100%", "height": "100px"}
            ),
            dbc.Button("Submit", id="upload_button", n_clicks=0),
            html.Br(),
            dbc.Alert(color="danger", is_open=False, id="invalid_geometry_alert"),
            html.Br(),
            html.P("or upload csv file"),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='output-data-upload'),
        ]),
        dbc.Col([
            html.H4("Generated data"),
            html.Br(),
            html.Div([
                dcc.Loading(
                    id="loading_plot",
                    type="default",
                    children=[
                        dcc.Graph(
                            id="ndvi_plot",
                            figure=fig_ndvi,
                            style={"backgroundColor": "transparent"} 
                        ),
                        dcc.Graph(
                            id="ndmi_plot",
                            figure=fig_ndmi,
                            style={"backgroundColor": "transparent"} 
                        )
                    ]
                )
            ])
        ])
    ]),
    html.Br(),
    dbc.Row(html.H4("Planting cycles and moisture levels")),
    dbc.Row([
        dbc.Col([
            html.P("From the NDVI and NDMI time-series curves generated for the submitted polygon(s), we are \
                   able to say the following regarding annual planting cycles and farm moisture levels:")
        ]),
        dbc.Col([])
    ])
])