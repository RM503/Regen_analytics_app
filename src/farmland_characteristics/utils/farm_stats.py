from typing import Any
import numpy as np
import pandas as pd
from .ndvi_peaks import ndvi_peaks_per_farm
from scipy.signal import savgol_filter, find_peaks
import logging 

logger = logging.getLogger(__name__)

def high_ndmi_days(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function generates an aggregate of high NDMI days
    for each polygon. 
    """
    NDMI_THRESHOLD = 0.38

    # Filter out high-NDMI farms based on threshold
    df_high_ndmi = df[df["ndmi"] > NDMI_THRESHOLD].copy()

    """ 
    In order to be more precise about water-stress levels of farms, we
    take into account the (annual) cumulative number of days spent in
    high-NDMI zones.
    """
    df_high_ndmi["year"] = df_high_ndmi["date"].dt.year

    df_high_ndmi_days = (
        df_high_ndmi.groupby(["uuid", "region", "year"], as_index=False)
        .apply(lambda g: pd.Series({
            "high_ndmi_days": (g["date"].max() - g["date"].min()).days
        }))
    )

    return df_high_ndmi_days

def calculate_farm_stats(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    This function generates summary statistics relevant to selected
    farmlands by analysing the NDVI and NDMI time-series data.
    """
    try:
        required_cols = ["uuid", "date", "ndvi", "ndmi"]
        if not pd.Series(required_cols).isin(df.columns).all():
            raise ValueError("Required columns are not present in the dataframe.")
    except ValueError as e:
        logging.error(e)

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    
    if df["region"].isna().any():
        df["region"] = df["region"].fillna("Unknown")

    # Round the areas to 3 decimal places
    if not df["area (acres)"].isna().any():
        df["area (acres)"] = df["area (acres)"].round(3)

    WINDOW_SIZE = 7
    POLY_ORDER = 3

    # Smooth the time-series data
    df["ndvi"] = df.groupby("uuid")["ndvi"].transform(lambda x: savgol_filter(x, WINDOW_SIZE, POLY_ORDER))
    df["ndmi"] = df.groupby("uuid")["ndmi"].transform(lambda x: savgol_filter(x, WINDOW_SIZE, POLY_ORDER))

    df_list = []

    """
    Here we assign peaks to each NDVI and NDMI time-series per uuid.
    The peak-finding parameters are, in no way, optimized. 
    """
    for _, group in df.groupby("uuid"):
        group = group.reset_index(drop=True)
        peaks, _ = find_peaks(
            group["ndvi"].values, 
            height=(0.4, 1.0), 
            prominence=0.20, 
            distance=10
        )
        group["peak"] = np.isin(group.index, peaks).astype(int)
        df_list.append(group)

    df_concat = pd.concat(df_list, ignore_index=True)
    
    df_concat["year"] = df_concat["date"].dt.year
    df_concat["month"] = df_concat["date"].dt.month

    df_ndvi_peak = df_concat[df_concat["peak"]==1].copy() 
    df_ndvi_peak_agg = df_ndvi_peak.groupby(["uuid", "year"]).agg(
        region=pd.NamedAgg(column="region", aggfunc="first"),
        area=pd.NamedAgg(column="area (acres)", aggfunc="first"),
        ndvi_peak_month=pd.NamedAgg(column="month", aggfunc=lambda x: " ".join(map(str, sorted(set(x)))) ),
        num_planting_cycles=pd.NamedAgg(column="ndvi", aggfunc="count")
    ).reset_index()

    df_ndvi_max = (
        df_concat.groupby(["uuid", "year", "region"])["ndvi"]
        .max()
        .reset_index(name="ndvi_max")
    
    )

    df_ndmi_max = (
        df_concat.groupby(["uuid", "year"])["ndmi"]
        .max()
        .reset_index(name="ndmi_max")
    )
    df_ndmi_max["moisture_level"] = df_ndmi_max["ndmi_max"].apply(
            lambda x: "high" if x >=0.38 else "medium" if 0.25 <= x < 0.38 else "approaching low" if 0.20 <= x < 0.25 else "low"
        )

    df_stats = df_ndvi_peak_agg.merge(df_ndmi_max, on=["uuid", "year"], how="inner").drop(columns=["ndmi_max"])
    df_stats.rename(
        columns={
            "area": "area (acres)",
            "ndvi_peak_month": "peak growth months",
            "num_planting_cycles": "number of planting cycles",
            "moisture_level": "moisture level"
        }, inplace=True
    )

    df_peakvidistribution = df_ndvi_max.merge(df_ndmi_max, on=["uuid", "year"], how="inner")
    df_peakvidistribution = df_peakvidistribution[["uuid", "year", "region", "ndvi_max", "ndmi_max"]]

    df_highndmidays = high_ndmi_days(df)
    df_ndvipeaksperfarm = ndvi_peaks_per_farm(df)

    # Return a serialized version of the dataframe to be kept in dcc.Store()
    
    return {
        "df_stats": df_stats.to_dict("records"),
        "df_peakvidistribution": df_peakvidistribution.to_dict("records"),
        "df_highndmidays": df_highndmidays.to_dict("records"),
        "df_ndvipeaksperfarm": df_ndvipeaksperfarm.to_dict("records")
    }