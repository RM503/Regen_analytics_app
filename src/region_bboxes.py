# Script for retrieving region bounding boxes from Supabase

import logging
import os 
from typing import Any

from shapely import wkt
from shapely.geometry import Point
from supabase import create_client

logging.basicConfig(level=logging.INFO)

# API keys are read from global environment variable updates
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def parse_centroid(centroid_str: str) -> Point:
    # This function fixes string format centroids into Shapely `POINT` objects.
    centroid_str = centroid_str.strip()

    if centroid_str.upper().startswith("POINT"):
        # Already proper WKT
        return wkt.loads(centroid_str)
    
    # Remove parentheses if present
    centroid_str = centroid_str.strip("()")

    # Split on comma if present, else split on whitespace
    if "," in centroid_str:
        lon_str, lat_str = centroid_str.split(",")
    else:
        lon_str, lat_str = centroid_str.split()

    lon, lat = float(lon_str), float(lat_str)
    return Point(lon, lat)

def region_bboxes_to_geojson() -> dict[str, Any] | None:
    # This function converts Supabase rows into readable GeoJSON format.
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Retrieve region names, centroids and geometries
        rows = client.table("regionbboxes").select("*").execute().data
        features = []

        # Convert retrieved rows to GeoJSON
        for row in rows:
            feature = {
                "type": "Feature",
                "geometry": row["geometry"],  # polygon/multipolygon
                "properties": {
                    "region": row["region"],
                    "centroid_point": row["centroid_point"]
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        logging.error(f"Failed to create Supabase client: {e}")
        return None
    
def generate_location_w_coords(region_geojson: dict[str, Any]) -> dict[str, list[float]]:
    """
    This function creates the `location_w_coords` dictionary
    by reading the `region_bboxes.geojson` file.
    """

    # Add the `Default` location
    location_w_coords = {
        "Default": [1.00, 38.00]
    }

    for feature in region_geojson["features"]:
        region = feature["properties"]["region"]
        centroid = parse_centroid(feature["properties"]["centroid_point"]) # Convert wkt to geometry

        lon = centroid.x 
        lat = centroid.y 

        location_w_coords[region] = [lat, lon]

    return location_w_coords