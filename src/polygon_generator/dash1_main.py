# Dashboard app with callbacks for `Polygon Generator` page
from datetime import datetime
import json
import logging
from typing import Any
from uuid import uuid4

import dash
from dash import Dash, dash_table, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dotenv
from flask import Flask
from flask import session
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from sqlalchemy import text

from auth.db import engine
from auth.supabase_auth import get_supabase_client
from config import USE_LOCAL_DB, LOCAL_DB_CONFIG
from db.db_utils import db_connect
from .layout import layout

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

if USE_LOCAL_DB:
    logging.info(
        f"Running in LOCAL mode — connecting to PostgreSQL at "
        f"{LOCAL_DB_CONFIG['host']}:{LOCAL_DB_CONFIG['port']}, "
        f"database '{LOCAL_DB_CONFIG['database']}'."
    )
else:
    logging.info("Running in SUPABASE mode.")

def init_dash1(server: Flask) -> Dash:
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/polygon_generator/", 
        external_stylesheets=[dbc.themes.DARKLY],
    )

    app.title = "Polygon Generator"
    app.layout = layout
    # Callbacks

    @app.callback(
        Output("map", "center"),
        Output("marker-layer", "children"),
        Input("location_dropdown", "value")
    )
    def toggle_map(location: str) -> tuple[list[float], list]:
        """
        This function controls map toggle from the location drop-down menu.
        The `Default` location refers to the centroid coordinates of Kenya.
        """
        location_w_coords = {
            "Default": [1.00, 38.00],
            "Kajiado_1": [-2.8072, 37.5271],
            "Kajiado_2": [-3.0318, 37.7068],
            "Laikipia_1": [0.2580, 36.5353],
            "Trans_Nzoia_1": [1.0199, 35.0211]
        }

        coords = location_w_coords.get(location, [1.00, 38.00])
        marker = dl.Marker(position=coords, children=dl.Popup(location or "Default")) # Marker placed at toggled location
        return coords, [marker]

    @app.callback(
        Output("vector-layer", "data"),
        Input("location_dropdown", "value")
    )   
    def update_vector_layer(location: str) -> dict[str, Any]:
        """
        This function updates location toggles to associated vector layers.
        """
        # The `Default` location has no associated vector layer
        if location == "Default":
            return {"type": "FeatureCollection", "features": []}

        query = text(
            "SELECT uuid, region, area, geometry FROM farmpolygons WHERE region = :region"
        )
        with engine.connect() as conn:
            gdf = gpd.read_postgis(query, conn, geom_col="geometry", params={"region": location})

        geojson_data = json.loads(gdf.to_json()) # Convert gdf to geojson

        # Include properties for tooltip features upon hovering
        for feature in geojson_data["features"]:
            props = feature["properties"]
            uuid = props.get("uuid", "N/A")
            area = props.get("area", "N/A")

            try:
                area_float = float(area)
                area_str = f"{area_float:.2f}"
            except (ValueError, TypeError):
                area_str = str(area)

            props["popup"] = f"uuid: {uuid}<br>Area: {area_str} acres"
        return geojson_data
        
    @app.callback(
        Output("geojson-output", "children"),
        Output("polygon_count_alert", "is_open"),
        Output("polygon_count_alert", "children"),
        Output("area_limit_alert", "is_open"),
        Output("area_limit_alert", "children"),
        Output("polygons_store", "data"),
        Input("edit_control", "geojson"), 
        Input("location_dropdown", "value")
    )
    def update_output(
            geojson: dict, 
            location: str
        ) -> tuple[str | dict[str, Any], bool, str, bool, str, str | dict[str, Any]]:
        """
        This function displays the geometries polygons drawn on
        the map, with a maximum of five polygons allowed.
        """
        MAX_POLYGONS = 5
        MAX_AREA = 3000 # in acres
        if geojson and "features" in geojson:
            wkt_list = []
            polygon_dict = {
                "uuid": [],
                "region": [],
                "area": [],
                "geometry": []
            }

            # Alert messages are empty by default; triggered only when conditions are met
            show_count_alert = False
            count_alert_message = ""

            show_area_alert = False
            area_alert_message = ""

            for i, feature in enumerate(geojson["features"]):
                if i < MAX_POLYGONS:
                    geom = feature.get("geometry")
                    if geom:
                        try:
                            polygon = shape(geom)

                            # Project to Mercator for calculating physics area
                            projection = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform 
                            projected = transform(projection, polygon)

                            #area = polygon.area * (111_000**2) * 0.000247105 # area in acres (rough conversion to physical distance)
                            area = projected.area * 0.000247105
                            
                            if area > MAX_AREA:
                                show_area_alert = True
                                area_alert_message = f"⚠️ Polygon {i+1} exceeds area limit of {MAX_AREA} acres and was not added."
                                
                                continue
                            
                            wkt = polygon.wkt
                            wkt_list.append(f"polygon {i+1}:\n{wkt}\n")
                            # Append to polygon_dict
                            polygon_dict["uuid"].append(str(uuid4()))
                            polygon_dict["region"].append(location)
                            polygon_dict["area"].append(area)
                            polygon_dict["geometry"].append(wkt)

                        except Exception as e:
                            logging.error(f"Error processing polygon {i+1}: {e}")
                else:
                    show_count_alert = True
                    count_alert_message = "⚠️ You can only draw up to 5 polygons."
            
            polygon_df = pd.DataFrame(polygon_dict)
            polygon_table = dash_table.DataTable(
                data=polygon_df.to_dict("records"),
                columns=[{"name": i, "id": i} for i in polygon_dict.keys()],
                style_table={"backgroundColor": "#212529", "color": "white"},
                style_cell={"backgroundColor": "#212529", "color": "white"}
            )

            return (
                polygon_table,
                show_count_alert, count_alert_message,
                show_area_alert, area_alert_message,
                polygon_df.to_dict("records")
            )

        return "", True, "No polygons drawn yet.", False, "", ""

    @app.callback(
        Output("download_button", "disabled"),
        Input("polygons_store", "data")
    )
    def enable_download_button(stored_data: dict[str, Any]) -> bool:
        # Enables download button only when selected polygon data are displayed
        if not stored_data:
            return True
        
        return False
    
    @app.callback(
        Output("download_polygons", "data"),
        Input("download_button", "n_clicks"),
        State("polygons_store", "data"),
        prevent_initial_call=True
    )
    def download_polygons(n_clicks: int, stored_data: dict[str, Any]) -> Any:
        if stored_data:
            df = pd.DataFrame(stored_data)
            df.rename(columns={"area": "area (acres)"}, inplace=True)
            return dcc.send_data_frame(df.to_csv, "polygons.csv", index=False)
        return dash.no_update
    
    @app.callback(
        Output("token_store", "data"),
        Input("token_interval", "n_intervals")
    )
    def store_token(_) -> str | None:
        # Stores access token to dcc.Store in layout
        token = session.get("access_token")

        return token
    
    @app.callback(
        Output("insert_button", "disabled"),
        Input("token_store", "data"),
        Input("polygons_store", "data"),
    )
    def enable_insert_button(token: str, stored_data: dict[str, Any]) -> bool:
        """
        This function enables the INSERT button only when the user
        is authenticated and authenticated user selects polygons.
        """
        # Condition 1: user not authenticated
        if not token:
            return True  # disabled

        # Condition 2: authenticated but no polygons yet
        if not stored_data:
            return True  # disabled

        # Both conditions met
        return False  
    
    @app.callback(
        Output("insert_notification", "children"),
        Output("insert_notification", "color"),
        Output("insert_notification", "is_open"),
        Input("insert_button", "n_clicks"),
        State("token_store", "data"),
        State("polygons_store", "data"),
        prevent_initial_call=True
    )
    def insert_polygons(n_clicks: int, token: str, stored_data: dict[str, Any]) -> tuple[str, str, bool]:
        """
        This function inserts the polygons chosen using the interactive
        tile-map into the `farmpolygons` table. This is only applicable
        to authenticated users.

        Args: (i) n_clicks - triggered by mouse click
              (ii) token - login access token
              (iii) stored_data - selected polygons

        Returns: Status message of the insert operation
        """
        TABLE_NAME = "farmpolygons"
        try:

            if USE_LOCAL_DB:
                conn = db_connect()
                
                with conn.cursor() as cursor:
                    for row in stored_data:
                        row.setdefault("created_at", datetime.now().isoformat())

                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['%s'] * len(row))
                        values = tuple(row.values())

                        query = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
                        cursor.execute(query, values)

                    logger.info(f"Inserted {len(stored_data)} polygons successfully.")
                    return f"Inserted {len(stored_data)} polygons successfully.", "success", True

            else:
                client = get_supabase_client()
                # Add timestamp
                for item in stored_data:
                    item["created_at"] = datetime.now().isoformat()

                response = client.table(TABLE_NAME).insert(stored_data).execute()

                if response.data:
                    logger.info(f"Inserted {len(response.data)} polygons successfully.")
                    return f"Inserted {len(response.data)} polygons successfully.", "success", True
                else:
                    logger.error(f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}")
                    return f"Insert failed: {response.error if hasattr(response, 'error') else 'Unknown error'}", "danger", True

        except Exception as e:
            logger.error(f"Error inserting polygons: {e}"), "danger", True
    
    return app