from dash import Dash
import dash_bootstrap_components as dbc
from dash import Output, Input
from shapely.geometry import shape
from src.frontend.layout import layout

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sentinel-2 App"
app.layout = layout 

@app.callback(
    Output("geojson-output", "children"),
    Output("polygon_count_alert", "is_open"),
    Output("polygon_count_alert", "children"),
    Input("edit_control", "geojson")
)
def update_output(geojson: dict):
    if geojson and "features" in geojson:
        wkt_list = []
        show_alert = False
        alert_message = ""

        for i, feature in enumerate(geojson["features"]):
            if i < 5:
                geom = feature.get("geometry")
                if geom:
                    try:
                        wkt = shape(geom).wkt
                        wkt_list.append(f"polygon {i+1}:\n{wkt}\n")
                    except Exception as e:
                        print(f"Error processing polygon {i+1}: {e}")
            else:
                show_alert = True
                alert_message = "⚠️ You can only draw up to 5 polygons."

        return "\n\n".join(wkt_list), show_alert, alert_message

    return "", True, "No polygons drawn yet."

if __name__ == "__main__":
    app.run(debug=True)