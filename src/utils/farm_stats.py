import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, find_peaks

logger = logging.getLogger(__name__)

class FarmDataProcessor:
    # Class containing methods required for preprocessing VI time-series data
    def __init__(self, window_size: int=7, poly_order: int=3):
        # Initialize parameters for Savitzky-Golay filter
        self.window_size = window_size
        self.poly_order = poly_order

    def _safe_smoothing(self, s: pd.Series) -> pd.Series:
        """
        This method checks if Savitzky-Golay filter is safe by checking the
        length of the time-series data against the window size.

        Args: (i) s - the time-series as a pandas series object

        Returns: Returns a smoothed version only if the length of s is greater than window size.
        """
        if len(s) <= self.window_size:
            return s
        return savgol_filter(s, self.window_size, self.poly_order)

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        This method performs the preprocessing steps on the time-series
        dataframe.
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

        df["ndvi"] = df.groupby("uuid")["ndvi"].transform(self._safe_smoothing)
        df["ndmi"] = df.groupby("uuid")["ndmi"].transform(self._safe_smoothing)

        return df 
    
class FarmStatsCalculator:
    # Class that contains methods for performing farm statistics calculations.
    def __init__(self, processor: FarmDataProcessor):
        self.processor = processor

    def _high_ndmi_days(self, df: pd.DataFrame) -> pd.DataFrame:
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
    
    def _ndvi_peaks_per_farm(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        This function groups NDVI time-series data by uuid and applies peak-finding algorithm
        in order to identify NDVI peaks occurring in each identified farm.
        """
        peaks_date_dict = {} # dict storing dates of identified peaks
        peaks_val_dict = {} # dict storing values of identified peaks

        for uuid, group in df.groupby("uuid"):
            group = group.reset_index(drop=True)
            peaks, _ = find_peaks(
                group["ndvi"].values,
                height=(0.4, 1.0),
                prominence=0.20,
                distance=10
            )

            # Checks which group indices are present in peaks; converts to binary
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
        # Find maximum length of array in peaks_dict to pad smaller ones
        max_length = max(len(v) for v in peaks_date_dict.values())

        # Padding all lists to the same length
        peaks_date_dict_padded = {
            k: v + [None] * (max_length - len(v)) for k, v in peaks_date_dict.items()
        }
        peaks_val_dict_padded = {
            k: v + [None] * (max_length - len(v)) for k, v in peaks_val_dict.items()
        }

        # Convert padded dicts to dataframes
        df_peaks_date = pd.DataFrame(peaks_date_dict_padded)
        df_peaks_val = pd.DataFrame(peaks_val_dict_padded)

        # Convert the wide form df to long form
        df_peaks_date["index"] = range(max_length)
        df_peaks_val["index"] = range(max_length)

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

        # Add back the `region` column
        df_regions = df[['uuid', 'region']].drop_duplicates()
        df_merged = df_merged.merge(df_regions, on='uuid', how='left')

        return df_merged

    def calculate_stats(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        df_processed = self.processor.preprocess(df)
        
        df_list = []

        """
        Here we assign peaks to each NDVI and NDMI time-series per uuid.
        The peak-finding parameters are, in no way, optimized. 
        """
        for _, group in df_processed.groupby("uuid"):
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

        df_highndmidays = self._high_ndmi_days(df)
        df_ndvipeaksperfarm = self._ndvi_peaks_per_farm(df)

        # Return a serialized version of the dataframe to be kept in dcc.Store()
        
        return {
            "df_stats": df_stats.to_dict("records"),
            "df_peakvidistribution": df_peakvidistribution.to_dict("records"),
            "df_highndmidays": df_highndmidays.to_dict("records"),
            "df_ndvipeaksperfarm": df_ndvipeaksperfarm.to_dict("records")
        }
