import glob
from typing import Type
import pandas as pd
import geopandas as gpd
from sqlmodel import SQLModel, Session 
from sqlalchemy.engine import Engine
from geoalchemy2.shape import from_shape
import logging

logging.basicConfig(level=logging.INFO)

def concat_gdf_regions(data_dir: str) -> gpd.GeoDataFrame:
    """
    This function takes a directory containing multiple gdf files of a similar
    type but of different regions and concatenates them into one.
    """
    file_paths = glob.glob(f"{data_dir}/*.feather")

    gdf_list = []
    for path in file_paths:
        REGION = path.split("/")[-1].split("_results")[0]

        gdf = gpd.read_feather(path, columns=["uuid", "area (acres)", "geometry"])
        gdf.insert(1, "region", REGION)
        gdf.rename(columns={"area (acres)" : "area"}, inplace=True)

        # Append to list 
        gdf_list.append(gdf)

    gdf_concat = pd.concat(gdf_list, ignore_index=True)
    return gdf_concat

def populate_table_rows(
        data: pd.DataFrame | gpd.GeoDataFrame,
        table_class: Type[SQLModel],
        engine: Engine
    ) -> None:
    
    if isinstance(data, gpd.GeoDataFrame):
        if not data["geometry"].is_valid.all():
            logging.warning("Not all geometries are valid.")

        if data.crs is None:
            logging.warning("CRS is missing. Setting it to `EPSG:4326`.")

            # Set CRS
            data.set_crs("EPSG:4326")

        # Convert shapely geometries to WKBElement for GeoAlchemy2
        # PostGIS will store geometries in WKB hex format, which needs to be decoded later
        data = data.copy()
        data["geometry"] = data["geometry"].apply(lambda geom: from_shape(geom, srid=4326))

    # Create row objects to populate the table using .iterrows() method
    objects = [table_class(**row.to_dict()) for _, row in data.iterrows()]

    """
    All the rows are added to table corresponding to the model class. If the
    same uuid rows are being added by mistakenly, they will be rejected.
    """
    with Session(engine) as session:
        session.add_all(objects)
        session.commit()