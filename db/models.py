# dB tables
from typing import Optional, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from geoalchemy2 import Geometry

class FarmPolygons(SQLModel, table=True):
    # Table for storing farm polygons

    uuid: str = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None)
    area: Optional[float] = Field(default=None)
    geometry: Optional[Any] = Field(
        sa_column=Column(Geometry(geometry_type="POLYGON", srid=4326))
    )