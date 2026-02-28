import logging
from typing import Any
from uuid import uuid4

import pandas as pd
from dash import dash_table, Input, Output 
from pyproj import Transformer
from shapely.geometry import shape 
from shapely.ops import transform

OutputType = tuple[str | dict[str, Any], bool, str, bool, str, str | dict[str, Any]]

def register(app):
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
    def run(geojson: dict, location: str) -> OutputType:
        """
        This function displays the geometries polygons drawn on
        the map, with a maximum of five polygons allowed.
        """
        MAX_POLYGONS = 5
        MAX_AREA = 3000 # in acres
        if geojson and "features" in geojson:
            wkt_list = []
            polygon_dict = {"uuid": [], "region": [], "area": [], "geometry": []}

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