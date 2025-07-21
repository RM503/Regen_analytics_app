import os 
import dotenv
import pandas as pd
from dash import Dash, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from sqlmodel import create_engine
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from .layout import layout
import logging 

logger = logging.getLogger(__name__)

app = Dash(__name__, requests_pathname_prefix="/dash3/", external_stylesheets=[dbc.themes.DARKLY])
app.title = "Farmland analytics"
app.layout = layout

dotenv.load_dotenv()

# Create SQLAlchemy engine
try:
    DB_URL = os.getenv("DB_URL")
    engine = create_engine(DB_URL, echo=True)
except OperationalError as e:
    logging.error(f"Connection failed: {e}")

# Callbacks
@app.callback(
    Output("high_ndmi", "figure"),
    Input("location-dropdown", "value")
)
def high_ndmi_days(location: str) -> Figure:
    query = text("SELECT * FROM highndmidays WHERE region = :region")
    df = pd.read_sql(query, engine, params={"region": location})

    fig = go.Figure()
    for year in sorted(df["year"].unique()):
        fig.add_trace(go.Histogram(
            x=df[df["year"] == year]["high_ndmi_days"],
            name=str(year), 
            nbinsx=50,
            marker=dict(
            line=dict(
                color="white",
                width=1 
            )
        ))
    )
    fig.update_layout(
        title="Distribution of annual high NDMI occurrences",
        plot_bgcolor="#222",      
        paper_bgcolor="#222",     
        font=dict(color="white"),
        xaxis_title="High NDMI days",
        yaxis_title="Count",
        barmode="stack"
    )

    return fig

if __name__ == "__main__":
    app.run(debug=True)
