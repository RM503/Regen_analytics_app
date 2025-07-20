"""
Script for instantiating a project DB and populating it with tables
"""
import os 
import dotenv
import pandas as pd 
import geopandas as gpd 
from sqlmodel import SQLModel, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from models import FarmPolygons
import utils
import logging 

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

def create_table(engine: Engine) -> None:
    # Create table
    SQLModel.metadata.create_all(engine)

def main(data: pd.DataFrame | gpd.GeoDataFrame) -> None:
    # Perform database populating tasks here
    utils.populate_table_rows(data, FarmPolygons, engine)

if __name__ == "__main__":

    DB_URL = os.getenv("DB_URL")

    DIR = "../src/dash1/assets/"
    gdf = utils.concat_gdf_regions(DIR)

    try:
        engine = create_engine(DB_URL, echo=True)
        logging.info("Connected successfully.")
    except OperationalError as e:
        logging.info(f"Connection failed: {e}")

    create_table(engine)
    main(gdf)