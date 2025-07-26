""" 
This script procecesses NDVI and NDMI data generated from the GEE web app that is then
uploaded through the Streamlit interface. 
"""
import numpy as np
from numpy.typing import NDArray
import pandas as pd
from scipy.signal import savgol_filter
import pandera.pandas as pa
from pandera import DataFrameSchema, Column
from sklearn.ensemble import IsolationForest
import logging

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
        vi: str,
        resample_date: bool=True
    ) -> pd.DataFrame:
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # Fill in NaN with interpolate, ffill and bfill
    df[vi] = (
            df[vi].interpolate(method="linear")
            .bfill()
            .ffill()
        )

    WINDOW_SIZE = 7
    POLY_ORDER = 3

    df[vi] = savgol_filter(df[vi], WINDOW_SIZE, POLY_ORDER)

    # Find outliers and bfill the values
    df["outlier"] = find_outliers(df[vi])
    df.loc[df["outlier"] == -1, vi] = np.nan

    df_clean = (
            df.bfill()
              .drop(columns="outlier")
        )

    # This VI indices are between -1 to 1. More extreme values are capped appropriately.

    df_clean.loc[df_clean[vi] < -1.0, vi] = -1.0

    df_clean.loc[df_clean[vi] > 1.0, vi] = 1.0

    # Check if cleaned data conforms to required schema
    try:
        validator = VIDataValidation(vi)
        validator.validate(df_clean)
        logging.info("Data validation passed")

        return df_clean
    except pa.errors.SchemaErrors as e:
         logging.error(f"Data validation failed: {e}")