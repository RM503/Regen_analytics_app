# For parse file uploads
import base64
import io 
import pandas as pd
from dash import html

def parse_contents(contents: str, filename: str) -> pd.DataFrame:
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            "There was an error processing this file."
        ])

    return df