import numpy as np
import pandas as pd
from scipy.signal import find_peaks

def ndvi_peask_per_farm(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function groups NDVI time-series data by uuid and applies peak-finding algorithm
    in order to identify NDVI peaks occurring in each identified farm.
    """
    peaks_date_dict = {}
    peaks_val_dict = {}

    for uuid, group in df.groupby("uuid"):
        group = group.reset_index(drop=True)
        peaks, _ = find_peaks(
            group["ndvi"].values, 
            height=(0.4, 1.0), 
            prominence=0.20, 
            distance=10
        )

        group["peak"] = np.isin(group.index, peaks).astype(int)

        # Extract dates where NDVI peaks occur and corresponding NDVI values
        ndvi_peak_dates = group[group["peak"] == 1]["date"].tolist()
        ndvi_peak_values = group[group["peak"] == 1]["ndvi"].tolist()

        peaks_date_dict[uuid] = ndvi_peak_dates    
        peaks_val_dict[uuid] = ndvi_peak_values
    
    """ 
    peaks_dict contains arrays of unequal lengths and, as such, cannot be used
    to construct a dataframe. Hence, we need to pad all arrays to the same length.
    """
    max_len = max(len(v) for v in peaks_date_dict.values()) # Find length of longest entry

    # Padding all arrays to the same length
    peaks_date_dict_padded = {
        k: v + [None]*(max_len - len(v)) for k, v in peaks_date_dict.items()
    }
    df_peaks_date = pd.DataFrame(peaks_date_dict_padded)

    peaks_val_dict_padded = {
        k: v + [None]*(max_len - len(v)) for k, v in peaks_val_dict.items()
    }
    df_peaks_val = pd.DataFrame(peaks_val_dict_padded)

    # Convert the wide form df to long form
    df_peaks_date["index"] = range(max_len)
    df_peaks_val["index"] = range(max_len)

    df_peaks_date_melted = pd.melt(
        df_peaks_date, 
        id_vars="index", 
        var_name="uuid", 
        value_name="ndvi_peak_date"
    ).dropna()

    df_peaks_val_melted = pd.melt(
        df_peaks_val, 
        id_vars="index", 
        var_name="uuid", 
        value_name="ndvi_peak_value"
    ).dropna()

    df_merged = df_peaks_date_melted.merge(df_peaks_val_melted, on=["uuid", "index"], how="inner")
    df_merged = df_merged.drop(columns="index")

    # Add a cumulative count to assign an order label to the peaks (eg. 1st, 2nd, 3rd,... peak of the year)
    df_merged["year"] = df_merged["ndvi_peak_date"].dt.year 
    df_merged["peak_position"] = (df_merged.groupby(["uuid", "year"]).cumcount() + 1).astype("int")
    df_merged.drop(columns=["year"], inplace=True)

    return df_merged