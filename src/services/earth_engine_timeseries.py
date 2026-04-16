"""
Core module for Earth Engine time-series task
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import ee
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from shapely import wkt

from analytics.vi_preprocessing import clean_vi_series
from utils.logging_config import get_logger

logger = get_logger(__name__)

_EE_INITIALIZED = False
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
MAX_POLYGONS = 5
DEFAULT_LOOKBACK_YEARS = 5


def initialize_ee() -> None:
    """Initialize Earth Engine once per worker process."""
    global _EE_INITIALIZED

    if _EE_INITIALIZED:
        return

    service_account = os.getenv("EE_SERVICE_ACC_EMAIL") or os.getenv("EE_SERVICE_ACCOUNT")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not service_account:
        raise RuntimeError("Missing EE_SERVICE_ACC_EMAIL environment variable.")
    if not credentials_path:
        raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS environment variable.")
    if not Path(credentials_path).exists():
        raise RuntimeError(f"Google credentials file not found: {credentials_path}")

    credentials = ee.ServiceAccountCredentials(
        service_account,
        key_file=credentials_path,
    )
    ee.Initialize(credentials)
    _EE_INITIALIZED = True

def add_vi_indices(img: ee.Image) -> ee.Image:
    """Add NDVI and NDMI bands to a Sentinel-2 image."""
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
    ndmi = img.normalizedDifference(["B8", "B11"]).rename("ndmi")

    return img.addBands([ndvi, ndmi])


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


def _default_date_range() -> tuple[str, str]:
    today = date.today()
    start = today - relativedelta(years=DEFAULT_LOOKBACK_YEARS)

    return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def _build_roi(geometry_wkt: str) -> tuple[ee.Geometry, str]:
    if not isinstance(geometry_wkt, str):
        geometry_wkt = str(geometry_wkt)

    shapely_geometry = wkt.loads(geometry_wkt)

    if shapely_geometry.is_empty:
        raise ValueError("Geometry is empty.")
    if not shapely_geometry.is_valid:
        raise ValueError("Geometry is invalid.")

    return ee.Geometry(shapely_geometry.__geo_interface__), shapely_geometry.wkt


def _features_to_dataframe(features: list[dict], geometry_wkt: str) -> pd.DataFrame:
    if not features:
        raise ValueError("No Sentinel-2 observations found for this polygon/date range.")

    df = pd.DataFrame([feature.get("properties", {}) for feature in features])
    required_columns = {"date", "ndvi", "ndmi"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(f"Earth Engine response is missing columns: {sorted(missing_columns)}")

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df = (
        df[["date", "ndvi", "ndmi"]]
        .dropna(subset=["ndvi", "ndmi"], how="all")
        .sort_values("date")
        .drop_duplicates(subset="date", keep="first")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError("No usable NDVI/NDMI observations remained after cloud masking.")

    for vi in ("ndvi", "ndmi"):
        if df[vi].notna().sum() == 0:
            raise ValueError(f"No usable {vi.upper()} observations remained after cloud masking.")

    df = clean_vi_series(df, "ndvi")
    df = clean_vi_series(df, "ndmi")
    df.insert(1, "geometry", geometry_wkt)

    return df[["date", "geometry", "ndvi", "ndmi"]]


def get_vi_timeseries(geometry_wkt: str) -> pd.DataFrame:
    """
    Generate NDVI and NDMI time-series data for one WKT geometry.

    Returns a dataframe with date, geometry, ndvi, and ndmi columns.
    """
    initialize_ee()

    ee_roi, normalized_wkt = _build_roi(geometry_wkt)
    start_date, end_date = _default_date_range()

    logger.info("Fetching Sentinel-2 VI data from %s to %s.", start_date, end_date)

    img_collection = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(ee_roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
        .map(mask_cloud_and_shadow)
        .map(add_vi_indices)
    ).select(["ndvi", "ndmi"])

    def map_vi(img: ee.Image) -> ee.Feature:
        stats = img.reduceRegion(
            reducer=ee.Reducer.median(),
            geometry=ee_roi,
            scale=20,
            maxPixels=1e13,
            crs="EPSG:4326",
        )

        ndvi_data = stats.get("ndvi")
        ndmi_data = stats.get("ndmi")
        date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")

        return ee.Feature(None, {"date": date, "ndvi": ndvi_data, "ndmi": ndmi_data})

    vi_timeseries = ee.FeatureCollection(img_collection.map(map_vi))
    features = vi_timeseries.getInfo().get("features", [])

    return _features_to_dataframe(features, normalized_wkt)


def _validate_roi_dataframe(roi: pd.DataFrame) -> None:
    if roi.empty:
        raise ValueError("No polygons provided.")
    if len(roi) > MAX_POLYGONS:
        logger.error(f"Data contains more than {MAX_POLYGONS} polygons.")
        raise ValueError(f"Too many polygons provided (limit: {MAX_POLYGONS}).")
    if "geometry" not in roi.columns:
        raise ValueError("ROI dataframe must include a 'geometry' column.")


def combined_timeseries(roi: pd.DataFrame) -> pd.DataFrame:
    """
    Generate combined NDVI and NDMI time-series data for each ROI row.
    """
    initialize_ee()
    _validate_roi_dataframe(roi)

    df_list = []
    for _, row in roi.iterrows():
        df = get_vi_timeseries(row["geometry"])

        # If `uuid` exists in the uploaded file, no need to assign new ones
        uuid = row.get("uuid") if "uuid" in roi.columns else None
        if pd.isna(uuid):
            uuid = str(uuid4())

        df.insert(0, "uuid", uuid)
        df.insert(1, "region", row.get("region"))
        df.insert(2, "area (acres)", row.get("area (acres)", np.nan))
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)
