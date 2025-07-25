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

def main(data: pd.DataFrame | gpd.GeoDataFrame, table_class: Type[SQLModel], engine: Engine) -> None:
    # Perform database populating tasks here
    utils.populate_table_rows(data, table_class, engine)

if __name__ == "__main__":
    DB_URL = os.getenv("DB_URL")
    try:
        engine = create_engine(DB_URL, echo=True)
        logging.info("Connected successfully.")
    except OperationalError as e:
        logging.error(f"Connection failed: {e}")
        exit(1)

    data_to_model_map = {
        "high_ndmi_days": models.HighNDMIDays,  
        "moisture_content": models.MoistureContent,
        "ndvi_peaks_annual": models.NDVIPeaksAnnual,
        "ndvi_peaks_monthly": models.NDVIPeaksMonthly,
        "ndvi_peaks": models.NDVIPeaksPerFarm
    }

    create_table(engine)  

    for file_type, model in data_to_model_map.items():
        FILE = f"{file_type}.csv"
        file_path = f"data/{FILE}"
        
        if not os.path.exists(file_path):
            logging.warning(f"{file_path} not found, skipping...")
            continue

        logging.info(f"Processing {file_type}")
        data = utils.concat_data_by_region(FILE)
        main(data, model, engine)
        logging.info(f"Finished populating: {file_type}")
