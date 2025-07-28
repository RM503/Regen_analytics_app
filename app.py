"""
This is the main FastAPI backend that directs users to different
parts of the dashboard
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.templating import Jinja2Templates
from src.initial_market_data.dash0_main import app as dash0
from src.polygon_generator.dash1_main import app as dash1
from src.farmland_characteristics.dash2_main import app as dash2
from src.farmland_statistics.dash3_main import app as dash3
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

templates = Jinja2Templates(directory="templates") # Landing page template

"""
This is where the different dashboards are mounted
"""

# Frontend - landing page
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/logos", StaticFiles(directory="logos"), name="logos")

# Dashboards start form here
app.mount("/initial_market_data", WSGIMiddleware(dash0.server))
app.mount("/polygon_generator", WSGIMiddleware(dash1.server))
app.mount("/farmland_characteristics", WSGIMiddleware(dash2.server))
app.mount("/farmland_statistics", WSGIMiddleware(dash3.server))

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
