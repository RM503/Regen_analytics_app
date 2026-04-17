"""
Module for fetching soil properties from ISDA API
"""
import asyncio
import os
from typing import Any

import aiohttp
import geopandas as gpd
import pandas as pd
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
from shapely.wkt import loads

from utils.logging_config import get_logger

logger = get_logger(__name__)

#dotenv.load_dotenv(override=True)
USERNAME = os.getenv("isda_username")
PASSWORD = os.getenv("isda_password")

BASE_URL = "https://api.isda-africa.com"
SOIL_PROPERTIES = [
    "bulk_density",
    "calcium_extractable",
    "carbon_organic",
    "carbon_total",
    "clay_content",
    "iron_extractable",
    "magnesium_extractable",
    "nitrogen_total",
    "ph",
    "phosphorous_extractable",
    "potassium_extractable",
    "sand_content",
    "silt_content",
    "stone_content",
    "sulphur_extractable",
    "texture_class",
    "zinc_extractable"
] # List of soil properties to be requested from API

def get_lat_lon(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function extracts latitude and longitude by computing the 
    centroid of queried polygons.
    """
    gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(loads))
    gdf.crs = "EPSG:4326"

    gdf["centroid"] = gdf["geometry"].centroid
    gdf["lat"] = gdf["centroid"].apply(lambda x: x.y)
    gdf["lon"] = gdf["centroid"].apply(lambda x: x.x)

    df_w_lat_lon = pd.DataFrame(gdf.drop(columns=["geometry", "centroid"]))

    return df_w_lat_lon

async def get_access_token(session: ClientSession) -> str:
    # Obtain ISDA access token
    url = f"{BASE_URL}/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }

    async with session.post(url, data=payload) as response:
        data = await response.json()
        return data.get("access_token")

async def fetch_soil_property_data(
        session: ClientSession, 
        access_token: str, 
        lat: float, 
        lon: float,
        prop: str
    ) -> Any:
    """
    This function returns result for a particular soil property given coordinates.

    Args: session (ClientSession): AIOHTTP ClientSession
          access_token (str): ISDA access token
          lat (float): latitude coordinate
          lon (float): longitude coordinate
          prop (float): soil property to query
    
    Returns:
        (Any): soil property value
    """
    url = f"{BASE_URL}/isdasoil/v2/soilproperty?lat={lat}&lon={lon}&property={prop}&depth=0-20"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, headers=headers) as response:
        response.raise_for_status() # Obtain status of HTTP request
        data = await response.json()

        try:
            value = data["property"][prop][0]["value"]["value"]
        except ClientResponseError:
            value = None
        
        return value
    
async def fetch_soil_data(
        session: ClientSession, 
        access_token: str, 
        uuid: str,
        lat: float, 
        lon: float
 ) -> dict[str, Any]:
    """
    This function fetches all the required soil properties.

    Args: session (ClientSession): AIOHTTP ClientSession
          access_token (str) - ISDA access token
          uuid (str): polygon uuid
          lat (float): latitude coordinate
          lon (float): longitude coordinate

    Returns:
        (dict[str, Any]): dictionary of all soil properties and values
    """
    result = {"uuid": uuid}

    tasks =[
        fetch_soil_property_data(session, access_token, lat, lon, prop)
        for prop in SOIL_PROPERTIES
    ]

    values = await asyncio.gather(*tasks)
    result.update(dict(zip(SOIL_PROPERTIES, values)))

    return result

async def main(df: pd.DataFrame) -> pd.DataFrame:
    # Main function
    df_w_lat_lon = get_lat_lon(df)

    async with aiohttp.ClientSession() as session:
        access_token = await get_access_token(session)

        tasks = [
            fetch_soil_data(session, access_token, row["uuid"], row["lat"], row["lon"])
            for _, row in df_w_lat_lon.iterrows()
        ]
        results = await asyncio.gather(*tasks)

    df_results = pd.DataFrame(results)

    # Rename columns with appropriate units
    cols_to_rename = {
        "bulk_density": "bulk_density (g/cm^3)",
        "calcium_extractable": "calcium_extractable (ppm)",
        "carbon_organic": "carbon_organic (g/kg)",
        "carbon_total": "carbon_total (g/kg)",
        "clay_content": "clay_content (%)",
        "iron_extractable": "iron_extractable (ppm)",
        "magnesium_extractable": "magnesium_extractable (ppm)",
        "nitrogen_total": "nitrogen_total (g/ kg)",
        "ph": "ph",
        "phosphorous_extractable": "phosphorous_extractable (ppm)",
        "potassium_extractable": "potassium_extractable (ppm)",
        "sand_content": "sand_content (%)",
        "silt_content": "silt_content (%)",
        "stone_content": "stone_content (%)",
        "sulphur_extractable": "sulphur_extractable (ppm)",
        "texture_class": "texture_class",
        "zinc_extractable": "zinc_extractable (ppm)"
    }
    df_results.rename(columns=cols_to_rename, inplace=True)

    return df_results.to_dict("records")
