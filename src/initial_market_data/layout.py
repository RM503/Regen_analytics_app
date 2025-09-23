from dash import html, dcc
import dash_bootstrap_components as dbc 
import plotly.io as pio

new_custs_time_region = pio.read_json("src/initial_market_data/plots_json/new_custs_time_region.json")
total_sales_vol_time_region = pio.read_json("src/initial_market_data/plots_json/total_sales_vol_time_region.json")

layout = dbc.Container([
    dbc.Row([
        html.H1("Initial Market Data", style={"fontSize": "30px", "textAlign": "center"})
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id="new_custs_time_region",
                figure=new_custs_time_region
            )
        ], xs=12, md=6, lg=6),
        dbc.Col([
            dcc.Graph(
                id="total_sales_vol_time_region",
                figure=total_sales_vol_time_region
            )
        ], xs=12, md=6, lg=6)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Label("Purchases/Sales Per Region"),
            dcc.Dropdown(
                id="purchases_sales_dropdown",
                options=["Purchases", "Sales", "Total Sales Volume"],
                value="Purchases",
                style={
                    "width": "200px",
                    "backgroundColor": "#222",   # background of the dropdown
                    "color": "black",            # selected text color
                    "border": "1px solid #444",
                },
            )
        ]),
        dbc.Col([
            html.Label("Per Distributor"),
            dcc.Dropdown(
                id="distributor_dropdown",
                options=["Number of Farms", "Total Sales Volume"],
                value="Number of Farms",
                style={
                    "width": "200px",
                    "backgroundColor": "#222",   # background of the dropdown
                    "color": "black",            # selected text color
                    "border": "1px solid #444",
                },
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="purchases_sales_graph")
        ], xs=12, md=6, lg=6),
        dbc.Col([
            dcc.Graph(id="distributor_graph")
        ], xs=12, md=6, lg=6)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Win Rate Categories"),

            dcc.Dropdown(
                id="win_rate_dropdown",
                options=[
                    {"label": "Farm Size Category", "value": "Farm Size Category"},
                    {"label": "Sub-County", "value": "Sub-County"},
                    {"label": "Crop Type", "value": "Crop Type"},
                    {"label": "Problem/Opportunity", "value": "Problem/Opportunity"},
                    {"label": "Distributor Proximity", "value": "Distributor Proximity"}
                ],
                value="Farm Size Category",
                style={
                    "width": "200px",
                    "backgroundColor": "#222",
                    "color": "black",
                    "border": "1px solid #444",
                }
            ),

            dcc.Graph(
                id="win_rate_graph",
                style={
                    "height": "500px",       
                    "overflowY": "hidden",   
                    "marginTop": "20px"
                }
            )
        ], width=12, style={"overflow": "hidden"})  
    ])
], fluid=True, className="px-2 px-md-4 px-lg-5")