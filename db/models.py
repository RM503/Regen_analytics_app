# dB tables
from typing import Optional, Any
from datetime import datetime
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
class NDVIPeaksPerFarm(SQLModel, table=True):
    # Table for storing NDVI peaks per farm
    uuid: str = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None)
    ndvi_peak_date: Optional[datetime] = Field(default=None, primary_key=True)
    ndvi_peak_value: Optional[float] = Field(default=None)
    peak_position: Optional[int] = Field(default=None)

class NDVIPeaksMonthly(SQLModel, table=True):
    # Table for storing monthly NDVI peaks
    id: int = Field(default=None, primary_key=True)
    ndvi_peak_year: Optional[int] = Field(default=None)
    region: Optional[str] = Field(default=None)
    ndvi_peak_month: Optional[str] = Field(default=None)
    ndvi_peaks_per_month: Optional[int] = Field(default=None)

class NDVIPeaksAnnual(SQLModel, table=True):
    # Table for storing annual NDVI peaks
    id: int = Field(default=None, primary_key=True)
    ndvi_peak_year: Optional[int] = Field(default=None)
    region: Optional[str] = Field(default=None)
    number_of_peaks_per_farm: Optional[int] = Field(default=None)
    uuid_count: Optional[int] = Field(default=None)

class HighNDMIDays(SQLModel, table=True):
    # Table for storing high NDMI days
    uuid: str = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None, primary_key=True)
    high_ndmi_days: Optional[int] = Field(default=None)

class MoistureContent(SQLModel, table=True):
    # Table for storing moisture content
    id: int = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None)
    moisture_content: Optional[str] = Field(default=None)
    counts: Optional[int] = Field(default=None)

class PeakVIDistribution(SQLModel, table=True):
    # Table for storing ndvi, ndmi peaks
    uuid: str = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None)
    year: int = Field(default=None, primary_key=True)
    ndvi_max: Optional[float] = Field(default=None)
    ndmi_max: Optional[float] = Field(default=None)