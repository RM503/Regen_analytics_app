# Obtains NDVI and NDMI time-series from queried polygons
import os 
import dotenv
from uuid import uuid4
from typing import Dict, Any, NewType
import ee
import pandas as pd
from shapely.geometry import shape

import logging 

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT")

ee.Authenticate()
ee.Initialize(project=GEE_PROJECT)

# Type hints for WKT polygon data
WKTPolygon = NewType("WKTPolygon", str)
CSVText = NewType("CSVText", str)

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

def get_vi_timeseries(RoI: WKTPolygon | CSVText, vi: str="ndvi") -> pd.DataFrame:
    """
    This function generates NDVI and NDMI time-series data from polygon geometry(ies)
    provided by the user. The geometry data is provided in the WKT format.

    Args: (i) RoI - the region(s)-of-interest; polygon data can be passed either standalone or 
                    in a csv file with a geometry column
          (ii) vi - the vegetation index to generate; defaults to `ndvi` 

    Returns: pandas dataframe containing vi time-series for queried polygons
    """
    if not isinstance(RoI, ee.Geometry) or not isinstance(RoI, Dict[str, Any]):
        raise ValueError(f"{RoI} is not a valid ee.Geometry GeoJSON object.")

    if not isinstance(RoI, ee.Geometry):
        # Check for polygon geometry type
        RoI = ee.Geometry(RoI)

    START_DATE = "2020-01-01"
    END_DATE = "2024-12-31"

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

    # Remove duplicate dates (this can arise due to data acquisition), add uuid and geometry
    df = df.drop_duplicates(subset="date", keep="first")
    df.insert(0, "uuid", str(uuid4()))
    df.insert(0, "geometry", shape(RoI.getInfo()).wkt) # store geometry in WKt format

    return df