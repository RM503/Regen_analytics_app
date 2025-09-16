import json 
from shapely import wkt

def generate_location_w_coords() -> dict[str, list[float]]:
    """
    This function creates the `location_w_coords` dictionary
    by reading the `region_bboxes.geojson` file.
    """
    with open("src/polygon_generator/region_bboxes.geojson", "r") as f:
        data = json.load(f)

    # Add the `Default` location
    location_w_coords = {
        "Default": [1.00, 38.00]
    }

    for feature in data["features"]:
        region = feature["properties"]["region"]
        centroid = wkt.loads(feature["properties"]["centroid_point"]) # Convert wkt to geometry

        lon = centroid.x 
        lat = centroid.y 

        location_w_coords[region] = [lat, lon]

    return location_w_coords