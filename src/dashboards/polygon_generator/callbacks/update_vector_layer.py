import json
from typing import Any

import geopandas as gpd
from dash import Input, Output
from sqlalchemy import text

from auth.db import engine

def register(app):
    @app.callback(
        Output("vector-layer", "data"),
        Output("region_bboxes", "data"),
        Input("location_dropdown", "value")
    )   
    def run(location: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        This function updates location toggles to associated vector layers.
        """
        # Define empty FeatureCollection when nothing is returned
        empty_fc = {"type": "FeatureCollection", "features": []} 

        with open("src/dashboards/polygon_generator/region_bboxes.geojson", "r") as f:
            bboxes = json.load(f)

        bbox_feature = next(
            (feat for feat in bboxes.get("features", [])
            if feat.get("properties", {}).get("region") == location),
            None,
        )

        if bbox_feature:
            bbox_geojson = {"type": "FeatureCollection", "features": [bbox_feature]}
        else:
            bbox_geojson = empty_fc

        # The `Default` location has no associated vector layer
        if not location or location == "Default":
            return empty_fc, empty_fc

        query = text(
            "SELECT uuid, region, area, geometry FROM farmpolygons WHERE region = :region"
        )
        with engine.connect() as conn:
            gdf = gpd.read_postgis(query, conn, geom_col="geometry", params={"region": location})

        if gdf.empty:
            return empty_fc, bbox_geojson

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

        return geojson_data, bbox_geojson