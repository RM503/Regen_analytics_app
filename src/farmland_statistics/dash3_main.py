import logging
import os

from dash import Dash, Input, Output
import dash_bootstrap_components as dbc
import dotenv
from flask import Flask
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import create_engine

from .layout import layout

logger = logging.getLogger(__name__)

def init_dash3(server: Flask) -> Dash:
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/farmland_statistics/",
        external_stylesheets=[dbc.themes.DARKLY]
    )
    app.title = "Farmland analytics"
    app.layout = layout

    dotenv.load_dotenv(override=True)

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
    def plot_high_ndmi_days(location: str) -> Figure:
        query = text("SELECT * FROM highndmidays WHERE region = :region")
        df = pd.read_sql(query, engine, params={"region": location})

        fig = go.Figure()
        for year in sorted(df["year"].unique()):
            fig.add_trace(go.Histogram(
                y=df[df["year"] == year]["high_ndmi_days"],
                name=str(year),
                nbinsy=50,
                marker=dict(
                    line=dict(
                        color="white",
                        width=0.25
                    )
            ))
        )
        fig.update_layout(
            title="Distribution of high moisture-level occurrences",
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            xaxis_title="Number of farms",
            yaxis_title="High moisture-level days",
            barmode="stack"
        )

        return fig

    @app.callback(
        Output("ndvi_peak_monthly", "figure"),
        Input("location-dropdown", "value")
    )
    def plot_ndvi_peak_monthly(location: str) -> Figure:
        query = text("SELECT * FROM ndvipeaksmonthly WHERE region = :region")
        df = pd.read_sql(query, engine, params={"region": location})

        fig = go.Figure()
        for year in sorted(df["ndvi_peak_year"].unique()):
            fig.add_trace(
                go.Bar(
                    x=df[df["ndvi_peak_year"]==year]["ndvi_peak_month"],
                    y=df[df["ndvi_peak_year"]==year]["ndvi_peaks_per_month"],
                    name=str(year),
                    marker=dict(
                        line=dict(
                            color="white",
                            width=0.25
                        )
                    )
                )
            )
        fig.update_layout(
            title="Distribution of peak growing seasons",
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            xaxis_title="Month",
            yaxis_title="Number of green peaks",
            #barmode="stack"
        )

        return fig

    @app.callback(
        Output("ndvi_peak_annual", "figure"),
        Input("location-dropdown", "value")
    )
    def plot_ndvi_peak_annual(location: str) -> Figure:
        query = text("SELECT * FROM ndvipeaksannual WHERE region = :region")
        df = pd.read_sql(query, engine, params={"region": location})

        fig = go.Figure()
        for year in sorted(df["ndvi_peak_year"].unique()):
            fig.add_trace(
                go.Bar(
                    x=df[df["ndvi_peak_year"]==year]["number_of_peaks_per_farm"],
                    y=df[df["ndvi_peak_year"]==year]["uuid_count"],
                    name=str(year),
                    marker=dict(
                        line=dict(
                            color="white",
                            width=0.25
                        )
                    )
                )
            )
        fig.update_layout(
            title="Distribution of annual planting cycles",
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white"),
            xaxis_title="Number of planting cycles",
            yaxis_title="Number of farms"
        )

        return fig

    @app.callback(
        Output("moisture_level", "figure"),
        Input("location-dropdown", "value")
    )
    def plot_moisture_level(location: str) -> Figure:
        query = text("SELECT * FROM moisturecontent WHERE region = :region")
        df = pd.read_sql(query, engine, params={"region": location})

        fig = go.Figure(
            data=go.Pie(
                labels=df["moisture_content"].unique(),
                values=df["counts"]
            )
        )
        fig.update_traces(
            textinfo='label+percent',
            pull=[0, 0.1, 0, 0],
            marker=dict(
                line=dict(color="white", width=0.25)
                )
            )
        fig.update_layout(
            title="Moisture-level breakdown",
            plot_bgcolor="#222",
            paper_bgcolor="#222",
            font=dict(color="white")
        )

        return fig

    @app.callback(
        Output("choropleth_map", "figure"),
        Input("location-dropdown", "value"),
        Input("indicator-dropdown", "value")
    )
    def update_choropleth_map(location: str, map_indicator: str) -> Figure:
        if map_indicator == "ndmi_max":
            query = """
                SELECT
                    a.uuid,
                    u.region,
                    u.geometry,
                    a.ndvi_max,
                    a.ndmi_max
                FROM (
                    SELECT
                        uuid,
                        AVG(ndvi_max) AS ndvi_max,
                        AVG(ndmi_max) AS ndmi_max
                    FROM peakvidistribution
                    GROUP BY uuid, region
                ) a
                JOIN farmpolygons u
                    ON a.uuid = u.uuid
                WHERE u.region = %(region)s;
            """
        else:
            query = """
                SELECT * FROM soildata WHERE region = %(region)s;
            """

        gdf = gpd.read_postgis(query, engine, geom_col="geometry", params={"region": location})
        # gdf = gdf[["uuid", "region", "geometry", map_indicator]]
        gdf["id"] = gdf["uuid"]

        geojson = gdf.set_index("id").__geo_interface__


        fig = go.Figure(go.Choroplethmapbox(
            geojson=geojson,
            locations=gdf["id"],
            z=gdf[map_indicator],
            colorscale="rdylgn",
            marker_opacity=0.7,
            marker_line_width=0.5,
            featureidkey="id",
            colorbar = dict(
                title=map_indicator,
                bgcolor="#222",
                outlinecolor="white",
                outlinewidth=0.25,
                tickfont=dict(color="white"),
                title_font=dict(color="white")
            ),
            hovertemplate="<b>UUID:</b> %{location}<br><b>Value:</b> %{z}<extra></extra>"
        ))

        # Mapbox layout
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox_zoom=10,
            mapbox_center={"lat": gdf.geometry.centroid.y.mean(), "lon": gdf.geometry.centroid.x.mean()},
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

        return fig

    return app
