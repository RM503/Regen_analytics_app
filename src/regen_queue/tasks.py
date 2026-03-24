import pandas as pd

from .celery_app import celery_app
from utils.vi_timeseries import combined_timeseries

@celery_app.task(bind=True, name="task.fetch_timeseries")
def fetch_timeseries(self, df_roi_records: list[dict]) -> list[dict]:
   """Fetch VI data for given ROI"""
   df_roi = pd.DataFrame(df_roi_records)
   df = combined_timeseries(df_roi)

   return df.to_dict("records")
