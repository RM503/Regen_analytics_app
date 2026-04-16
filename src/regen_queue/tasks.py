import pandas as pd

from .celery_app import celery_app
from services.earth_engine_timeseries import combined_timeseries, initialize_ee

@celery_app.task(bind=True, name="task.fetch_timeseries")
def fetch_timeseries(self, df_roi_records: list[dict]) -> list[dict]:
    """Fetch VI data for given ROI."""
    initialize_ee()

    df_roi = pd.DataFrame(df_roi_records)
    df = combined_timeseries(df_roi)

    return df.to_dict("records")
