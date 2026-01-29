# Obtains NDVI and NDMI time-series from queried polygons
from datetime import date
import logging
import os 
from uuid import uuid4

from dateutil.relativedelta import relativedelta
import ee
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import shape

from .preprocessing import clean_vi_series

logger = logging.getLogger(__name__)

credentials = ee.ServiceAccountCredentials(
    os.environ["EE_SERVICE_ACC_EMAIL"],
    key_file=os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
)
ee.Initialize(credentials)

class VIIndex:
    """
    This class packages functions for calculating various vegetation indices. 
    The various functions are packaged as static methods.
    """
    @staticmethod
    def add_NDVI(img: ee.Image) -> ee.Image:
        """ 
        This function takes an ee.Image object and adds an NDVI band to it.

        Args: img - ee.Image object

        Returns: same ee.Image object with an NDVI band 
        """
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
        return img.addBands([ndvi])
    
    @staticmethod
    def add_NDMI(img: ee.Image) -> ee.Image:
        """ 
        This function takes an ee.Image object and adds an NDWI band to it. This uses
        the following NDWI convention

        NDMI = (NIR - SWIR) / (NIR + SWIR)

        Args: img - ee.Image object

        Returns: same ee.Image object with an NDWI band 
        """
        ndmi = img.normalizedDifference(["B8", "B11"]).rename("ndmi")
        return img.addBands([ndmi])

def mask_cloud_and_shadow(img: ee.Image) -> ee.Image:
    """ 
    This function creates a pixel mask that are deemed to be cloud
    and (or) cloud shadow using Sentinel-2 `MSK_CLDPRB` and
    `Scene Classification Layer`.

    Args: img - ee.Image object

    Returns: same ee.Image object with an updated mask
    """

    # Setting cloud probability to 30%
    cloud_prob = img.select("MSK_CLDPRB")
    snow_prob = img.select("MSK_SNWPRB")
    cloud = cloud_prob.lt(30)
    snow = snow_prob.lt(30)

    # Use SCL to select shadows and cirrus cloud masks
    scl = img.select("SCL")
    shadow = scl.eq(3)
    cirrus = scl.eq(10)

    mask = (
        cloud.And(snow)
        .And(cirrus.neq(1))
        .And(shadow.neq(1))
    )

    return img.updateMask(mask)

def get_vi_timeseries(RoI: str, vi: str) -> pd.DataFrame:
    """
    This function generates NDVI and NDMI time-series data from a polygon geometry
    provided by the user. The geometry data is provided in the WKT format.

    Args: (i) RoI - the region(-of-interest; polygon data must be passed either standalone
          (ii) vi - the vegetation index to generate; defaults to `ndvi` 

    Returns: pandas dataframe containing vi time-series for queried polygons
    """
    
    # Polygons are passed as wkt strings; need to be converted to ee.Geometry objects
    if not isinstance(RoI, str):
        RoI = str(RoI)

    shapely_polygon = wkt.loads(RoI)
    RoI = ee.Geometry.Polygon(shapely_polygon.__geo_interface__["coordinates"])

    """
    VI data is generated for a time year time span given current date.
    """
    today = date.today()
    five_years_ago = today - relativedelta(years=5)

    START_DATE = five_years_ago.strftime("%Y-%m-%d")
    END_DATE = today.strftime("%Y-%m-%d")

    vi_map = {
        "ndvi": VIIndex.add_NDVI,
        "ndmi": VIIndex.add_NDMI
    }
    
    img_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(START_DATE, END_DATE)
        .map(mask_cloud_and_shadow)
        .map(vi_map[vi])
        .filter(ee.Filter.bounds(RoI))
    ).select(vi)

    def map_vi(img: ee.Image) -> ee.Feature:
        stats = img.reduceRegion(
            reducer=ee.Reducer.median(),
            geometry=RoI,
            scale=10,
            maxPixels=1e13,
            crs="EPSG:4326"
        )
        
        vi_data = stats.get(vi)
        date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")

        return ee.Feature(None, {"date": date, vi: vi_data})
    
    vi_timeseries = ee.FeatureCollection(img_collection.map(map_vi))

    # Extract time-series data from the `properties` column
    df = (
        pd.DataFrame(vi_timeseries.getInfo()["features"])
        .drop(columns=["type", "geometry"])
    )

    # Unpack the properties column
    df[["date", vi]] = df["properties"].apply(pd.Series)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df = df[["date", vi]]

    # Remove duplicate dates (this can arise due to data acquisition), add geometry
    df = df.drop_duplicates(subset="date", keep="first")

    # Apply preprocessing steps
    df_cleaned = clean_vi_series(df, vi)
 
    df_cleaned.insert(2, "geometry", shape(RoI.getInfo()).wkt) # store geometry in WKt format

    return df_cleaned

def combined_timeseries(RoI: pd.DataFrame) -> pd.DataFrame:
    """
    This function combines the NDVI and NDVI data ...
    """
    max_polygons = 5
    def process_single_geometry(geometry: str) -> pd.DataFrame:

        df_ndvi = get_vi_timeseries(geometry, "ndvi")
        df_ndmi = get_vi_timeseries(geometry, "ndmi")
        df_merged = df_ndvi.merge(df_ndmi, on=["date", "geometry"], how="inner")
 
        return df_merged[["date", "geometry", "ndvi", "ndmi"]]

    if len(RoI) > max_polygons:
        logging.error(f"Data contains more than {max_polygons} polygons.")
        raise ValueError(f"Too many polygons provided (limit: {max_polygons}).")

    df_list = []
    for idx, row in RoI.iterrows():
        df = process_single_geometry(row["geometry"])

        # If `uuid` exists in the uploaded file, no need to assign new ones
        uuid = row["uuid"] if "uuid" in RoI.columns else str(uuid4())
        df.insert(0, "uuid", uuid)
        df.insert(1, "region", row["region"])
        df.insert(2, "area (acres)", row.get("area (acres)", np.nan))
        df_list.append(df)
   
    return pd.concat(df_list, ignore_index=True)
