""" 
This script procecesses NDVI and NDMI data generated from the GEE web app that is then
uploaded through the Streamlit interface. 
"""
import logging

import numpy as np
from numpy.typing import NDArray
import pandas as pd
import pandera.pandas as pa
from pandera import DataFrameSchema, Column
from scipy.signal import savgol_filter
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class VIDataValidation:
    """ 
    This class validates the preprocessed time-series data containing any
    vegetation index useful for the study.
    """
    def __init__(self, vi_index: str):
        self.vi_index = vi_index
        self.schema = self._build_schema()

    def _build_schema(self) -> DataFrameSchema:
        # Returns the desired dataframe schema
        return DataFrameSchema(
            {
                "uuid": Column(str, required=False),
                "date": Column(pa.DateTime, nullable=False),
                self.vi_index: Column(float, checks=pa.Check.in_range(-1, 1), nullable=True)
            }
        )
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.schema.validate(df)

    
def find_outliers(col: pd.Series) -> NDArray[np.float64]:
    """ 
    This function applies the Isolation Forest algorith on the
    time-series data for detecting possible outliers.

    The value for contamination must account for the natural variation
    in the data. We choose 0.025.
    """

    X = col.values.reshape(-1, 1) # Format input into required shape
    model = IsolationForest(
        n_estimators=150,
        contamination=0.075,
        random_state=10
    ) # Setting contamination
    model.fit(X)

    # Predictions will consist of two values: +1 for inliers and -1 for outliers
    Y_preds = model.predict(X)

    return Y_preds

def clean_vi_series(
        df: pd.DataFrame,
        vi: str
    ) -> pd.DataFrame:
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # Fill in NaN with interpolate, ffill and bfill
    df[vi] = (
            df[vi].interpolate(method="linear")
            .bfill()
            .ffill()
        )
    
    # **ADD LOGGING HERE**
    logging.info(f"Before outlier detection - NaN: {df[vi].isnull().sum()}, "
                 f"inf: {np.isinf(df[vi]).sum()}, "
                 f"min: {df[vi].min()}, max: {df[vi].max()}")
    
    # Find outliers and bfill the values
    df["outlier"] = find_outliers(df[vi])
    
    # **ADD LOGGING HERE**
    outlier_count = (df["outlier"] == -1).sum()
    logging.info(f"Outliers detected: {outlier_count}/{len(df)} ({100*outlier_count/len(df):.1f}%)")
    
    df.loc[df["outlier"] == -1, vi] = np.nan

    df_clean = (
            df.bfill()
              .ffill()
              .drop(columns="outlier")
        )
    
    # **ADD LOGGING HERE**
    logging.info(f"After bfill/ffill - NaN: {df_clean[vi].isnull().sum()}, "
                 f"inf: {np.isinf(df_clean[vi]).sum()}")
    
    # **ADD THIS CHECK**
    if df_clean[vi].isnull().any() or np.isinf(df_clean[vi]).any():
        logging.error(f"Still have invalid values! NaN indices: {df_clean[df_clean[vi].isnull()].index.tolist()}")
        logging.error(f"Data sample: {df_clean[[vi]].head(20)}")
        # Replace remaining invalid values
        df_clean[vi] = df_clean[vi].replace([np.inf, -np.inf], np.nan)
        df_clean[vi] = df_clean[vi].interpolate(method="linear").bfill().ffill()
        
        # Last resort: use median
        if df_clean[vi].isnull().any():
            df_clean[vi] = df_clean[vi].fillna(df_clean[vi].median())
    
    # Apply Savitzky-Golay filter
    WINDOW_SIZE = 15
    POLY_ORDER = 3
    
    if len(df_clean) >= WINDOW_SIZE:
        df_clean[vi] = savgol_filter(df_clean[vi], WINDOW_SIZE, POLY_ORDER)
    else:
        logging.warning("Skipping Savitzky–Golay filter due to short time series.")

    df_clean[vi] = df_clean[vi].clip(-1.0, 1.0)

    try:
        validator = VIDataValidation(vi)
        validator.validate(df_clean)
        logging.info("Data validation passed")

        return df_clean
    except pa.errors.SchemaErrors as e:
         logging.error(f"Data validation failed: {e}")
         raise