from dash import Dash 
import dash_bootstrap_components as dbc
from layout import layout

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "VI generator"
app.layout = layout 

if __name__ == "__main__":
    app.run(debug=True)