import logging

from dash import Dash, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask
from plotly.graph_objects import Figure
import plotly.io as pio

from .layout import layout 

logger = logging.getLogger(__name__)

def init_dash0(server: Flask) -> Dash:
    app = Dash(
        __name__, 
        server=server, 
        routes_pathname_prefix="/initial_market_data/", 
        external_stylesheets=[dbc.themes.DARKLY]
    )

    app.title = "Initial Market Research"
    app.layout = layout 

    @app.callback(
        Output("purchases_sales_graph", "figure"),
        Input("purchases_sales_dropdown", "value")
    )
    def purchase_sales_plots(item: str) -> Figure:
        if item == "Purchases":
            return pio.read_json("src/initial_market_data/plots_json/purchases_per_month_region.json")
        elif item == "Sales":
            return pio.read_json("src/initial_market_data/plots_json/sales_per_month_region.json")
        elif item == "Total Sales Volume":
            return pio.read_json("src/initial_market_data/plots_json/total_sales_vol_region.json")

    @app.callback(
        Output("distributor_graph", "figure"),
        Input("distributor_dropdown", "value")
    )    
    def per_distributor(item: str) -> Figure:
        if item == "Number of Farms":
            return pio.read_json("src/initial_market_data/plots_json/number_of_farms_per_distributor.json")
        elif item == "Total Sales Volume":
            return pio.read_json("src/initial_market_data/plots_json/sales_vol_per_distributor.json")

    @app.callback(
        Output("win_rate_graph", "figure"),
        Input("win_rate_dropdown", "value")
    )
    def win_rate_plots(item: str) -> Figure:
        file_map = {
            "Farm Size Category": "src/initial_market_data/plots_json/win_rate_farm_size.json",
            "Sub-County": "src/initial_market_data/plots_json/win_rate_subcounty.json",
            "Crop Type": "src/initial_market_data/plots_json/win_rate_crop_type.json",
            "Problem/Opportunity": "src/initial_market_data/plots_json/win_rate_problems.json",
            "Distributor Proximity": "src/initial_market_data/plots_json/win_rate_proximity.json",
        }

        fig = pio.read_json(file_map[item])
        fig.update_layout(height=500)  # Force consistent height
        return fig
    
    return app