from datetime import datetime
from dash import Dash, Input, Output, State 
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import shapely
from shapely.geometry import Polygon
from .layout import layout
from src.dash2.utils.vi_timeseries import combined_timeseries
import logging 

logger = logging.getLogger(__name__)

app = Dash(__name__, requests_pathname_prefix="/dash2/", external_stylesheets=[dbc.themes.DARKLY])
app.title = "VI generator"
app.layout = layout 

@app.callback(
    Output("invalid_geometry_alert", "is_open"),
    Output("invalid_geometry_alert", "children"),
    Output("geometry_validation_check", "data"),
    Input("upload_button", "n_clicks"),
    State("polygon_input", "value"),
    prevent_initial_call=True
)
def validate_input(n_clicks: int, polygon_wkt: str) -> tuple[bool, str, bool]:
    """
    This function is used to validate the type of geometry that can be typed
    into the submission box. It will throw an error if object is anything
    but a POLYGON geometry.
    """
    try:
        geom = shapely.wkt.loads(polygon_wkt)

        # Check instance type
        if isinstance(geom, Polygon):
            return False, "", True
        else:
            return True, f"❌ Input is not a single POLYGON. Detected: {type(geom).__name__}", False
    
    except Exception as e:
        return True, f"❌ Invalid WKT format: {str(e)}", False

@app.callback(
    Output("ndvi_plot", "figure"),
    Output("ndmi_plot", "figure"),
    Input("upload_button", "n_clicks"),
    State("polygon_input", "value"),
    State("geometry_validation_check", "data"),
    prevent_initial_call=True
)
def plot_vi_data(n_clicks: int, polygon_wkt: str, is_valid: bool) -> tuple[Figure, Figure]:
    """
    Depending on the validity check from the previous callback, the
    NDVI-NDMI time-series plots will be generated.
    """
    if not is_valid:
        # Return empty placeholder figure
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
        return fig_ndvi, fig_ndmi

    df = combined_timeseries(polygon_wkt)

    # Plot the data
    fig_ndvi = go.Figure()
    fig_ndvi.add_trace(
        go.Scatter(
            x=df["date"], y=df["ndvi"], mode="lines+markers", name="NDVI", connectgaps=True,
            marker=dict(line=dict(color="black", width=1))
        )
    )
    fig_ndmi = go.Figure()
    fig_ndmi.add_trace(
        go.Scatter(
            x=df["date"], y=df["ndmi"], mode="lines+markers", name="NDMI", connectgaps=True,
            marker=dict(line=dict(color="black", width=1))
        )
    )
    fig_ndvi.update_layout(
        xaxis_title="Date",
        yaxis_title="NDVI",
        xaxis=dict(tickformat="%Y-%m-%d"),
        plot_bgcolor="#222",
        paper_bgcolor="#222",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    fig_ndmi.update_layout(
        xaxis_title="Date",
        yaxis_title="NDMI",
        xaxis=dict(tickformat="%Y-%m-%d"),
        plot_bgcolor="#222",
        paper_bgcolor="#222",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig_ndvi, fig_ndmi

if __name__ == "__main__":
    app.run(debug=True)