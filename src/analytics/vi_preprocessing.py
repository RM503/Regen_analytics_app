from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.pandas as pa
from numpy.typing import NDArray
from pandera import DataFrameSchema, Column
from scipy.signal import savgol_filter
from sklearn.ensemble import IsolationForest

from utils.logging_config import get_logger

logger = get_logger(__name__)

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
    
def find_outliers(
        col: pd.Series,
        *,
        n_estimators: int = 150,
        contamination: float = 0.075,
        random_state: int = 10
) -> NDArray[np.float64]:
    """ 
    This function applies the Isolation Forest algorith on the
    time-series data for detecting possible outliers.

    The value for contamination must account for the natural variation
    in the data. We choose 0.025.
    """

    x = col.values.reshape(-1, 1) # Format input into required shape
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state
    ) # Setting contamination
    model.fit(x)

    # Predictions will consist of two values: +1 for inliers and -1 for outliers
    y_pred = model.predict(x)

    return y_pred

def clean_vi_series(
        df: pd.DataFrame,
        vi: str,
        window_size: int = 15,
        poly_order: int = 3
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
    logger.info(f"Before outlier detection - NaN: {df[vi].isnull().sum()}, "
                 f"inf: {np.isinf(df[vi]).sum()}, "
                 f"min: {df[vi].min()}, max: {df[vi].max()}")
    
    # Find outliers and bfill the values
    df["outlier"] = find_outliers(df[vi])
    
    # **ADD LOGGING HERE**
    outlier_count = (df["outlier"] == -1).sum()
    logger.info(f"Outliers detected: {outlier_count}/{len(df)} ({100*outlier_count/len(df):.1f}%)")
    
    df.loc[df["outlier"] == -1, vi] = np.nan

    df_clean = (
            df.bfill()
              .ffill()
              .drop(columns="outlier")
        )
    
    # **ADD LOGGING HERE**
    logger.info(f"After bfill/ffill - NaN: {df_clean[vi].isnull().sum()}, "
                 f"inf: {np.isinf(df_clean[vi]).sum()}")
    
    # **ADD THIS CHECK**
    if df_clean[vi].isnull().any() or np.isinf(df_clean[vi]).any():
        logger.error(f"Still have invalid values! NaN indices: {df_clean[df_clean[vi].isnull()].index.tolist()}")
        logger.error(f"Data sample: {df_clean[[vi]].head(20)}")
        # Replace remaining invalid values
        df_clean[vi] = df_clean[vi].replace([np.inf, -np.inf], np.nan)
        df_clean[vi] = df_clean[vi].interpolate(method="linear").bfill().ffill()
        
        # Last resort: use median
        if df_clean[vi].isnull().any():
            df_clean[vi] = df_clean[vi].fillna(df_clean[vi].median())
    
    # Apply Savitzky-Golay filter
    if len(df_clean) >= window_size:
        df_clean[vi] = savgol_filter(df_clean[vi], window_size, poly_order)
    else:
        logger.warning("Skipping Savitzky–Golay filter due to short time series.")

    df_clean[vi] = df_clean[vi].clip(-1.0, 1.0)

    try:
        validator = VIDataValidation(vi)
        validator.validate(df_clean)
        logger.info("Data validation passed")

        return df_clean
    except pa.errors.SchemaErrors as e:
         logger.error(f"Data validation failed: {e}")
         raise