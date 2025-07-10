from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Define blank canvas on which NDVI/NDMI time-seres are generated
fig = go.Figure()
fig.update_layout(
    width=600,
    height=300,
    plot_bgcolor="#222",      # dark plot area
    paper_bgcolor="#222",     # dark area outside plot
    font=dict(color="white"), # white text
    xaxis_title="Date",
    xaxis=dict(range=[datetime(2020, 1, 1), datetime(2024, 12, 31)], type="date"),
    yaxis_title="NDVI/NDMI",
    yaxis=dict(range=[-0.5, 1]),
    margin=dict(l=20, r=20, t=30, b=20),  # optional: reduce padding
)

layout = dbc.Container([
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
            html.P("Type polygon data in the box"),
            dcc.Textarea(
                id="polygon_input",
                value="Add polygon geometry here",
                style={"width": "100%", "height": "100px"}
            ),
            html.Button("Submit", id="upload_button", n_clicks=0),
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
            dcc.Graph(
                id="ndvi_plot",
                figure=fig,
                style={"backgroundColor": "transparent"} 
            )
        ])
    ])
])