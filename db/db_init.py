"""
Script for instantiating a project DB and populating it with tables
"""
import os 
import dotenv
from typing import Type
import pandas as pd 
import geopandas as gpd 
from sqlmodel import SQLModel, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
import models
import utils
import logging 

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

def create_table(engine: Engine) -> None:
    # Create table
    SQLModel.metadata.create_all(engine)

def main(data: pd.DataFrame | gpd.GeoDataFrame, table_class: Type[SQLModel]) -> None:
    # Perform database populating tasks here
    utils.populate_table_rows(data, table_class, engine)

if __name__ == "__main__":

    DB_URL = os.getenv("DB_URL")
    try:
        engine = create_engine(DB_URL, echo=True)
        logging.info("Connected successfully.")
    except OperationalError as e:
        logging.info(f"Connection failed: {e}")

    data_to_model_map = {
        "high_ndmi_days": models.HighNDMIDays,  
        "moisture_content": models.MoistureContent,
        "ndvi_peaks_annual": models.NDVIPeaksAnnual,
        "ndvi_peaks_monthly": models.NDVIPeaksMonthly,
        "ndvi_peaks": models.NDVIPeaksPerFarm
    }

    file_types = list(data_to_model_map.keys())

    for file_type in file_types:
        FILE = f"{file_type}.csv"
        data = utils.concat_data_by_region(FILE)

        model = data_to_model_map[file_type]
        
        create_table(engine)
        main(data, model)
