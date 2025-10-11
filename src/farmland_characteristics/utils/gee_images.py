# Scripts for generating GEE thumbnails of Sentinel-2 rasters
import ee
from shapely import from_wkt

def convert_wkt_to_ee_geometry(wkt: str) -> ee.Geometry:
    """
    This function converts WKT string representation of geometries
    into ee.Geometry objects for GEE.

    Args: (i) polygon geometry in WKT

    Returns: corresponding ee.Geometry object
    """
    shapely_polygon = from_wkt(wkt)
    x_coords, y_coords = shapely_polygon.exterior.coords.xy 

    xy_coords = [[x, y] for x, y in zip(x_coords, y_coords)]

    return ee.Geometry.Polygon(xy_coords)

def mask_s2_clouds(image: ee.Image) -> ee.Image:
    """
    This function performs cloud-masking by using the Q60 band
    of the Sentinel-2 data.

    Args: (i) image - an ee.Image object to be masked
    
    Returns: the image with clouds masked out.
    """
    qa = image.select("QA60")
    cloud_bit_mask = 1 << 10 # Opaque clouds
    cirrus_bit_mask = 1 << 11 # Cirrus clouds

    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
        qa.bitwiseAnd(cirrus_bit_mask).eq(0)
    )

    return image.updateMask(mask)

def get_image_dates(image_collection: ee.ImageCollection):

    # Generate timestamps from the image collection
    dates = (
        image_collection.aggregate_array("system:time_start")
                        .map(lambda time: ee.Date(time).format("YYYY-MM-dd"))
    )

    return dates.getInfo()

def get_rgb_image(geometry: ee.Geometry, START_DATE: str) -> ee.Image:
    """
    This function retrieves the least cloudy image of the given polygon
    at a specified 10-day window.
    """
    START_DATE = ee.Date(START_DATE)
    NEXT_DATE = START_DATE.advance(30, "day")

    # Get Sentinel-2 image collection, filter and sort by cloud cover
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(START_DATE, NEXT_DATE)
        .map(mask_s2_clouds)
        .sort("CLOUD_COVER")
    )

    # Take the first (least cloudy) image
    image = ee.Image(s2.first())

    # Select RGB bands
    rgb = image.select(["B4", "B3", "B2"]).clip(geometry)

    """
    Sentinel-2 surface reflectance data are stored as integers between 0 - 10000. Hence,
    they are scaled to unity.
    """
    rgb_scaled = rgb.divide(10000)

    return rgb_scaled
