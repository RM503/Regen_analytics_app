# Frontend - landing page

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.templating import Jinja2Templates
from src.dash1.dash1_main import app as dash1
from src.dash2.dash2_main import app as dash2
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/logos", StaticFiles(directory="logos"), name="logos")
app.mount("/dash1", WSGIMiddleware(dash1.server))
app.mount("/dash2", WSGIMiddleware(dash2.server))

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
