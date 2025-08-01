"""
This is the main FastAPI backend that directs users to different
parts of the dashboard
"""
import os
import dotenv
from typing import Annotated
from fastapi import Form, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.templating import Jinja2Templates
from supabase import create_client
from auth.supabase_auth import supabase_auth
from src.initial_market_data.dash0_main import app as dash0
from src.polygon_generator.dash1_main import app as dash1
from src.farmland_characteristics.dash2_main import app as dash2
from src.farmland_statistics.dash3_main import app as dash3
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

dotenv.load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

@app.post("/login")
async def post_login(
        email: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)]
    ) -> dict[str, str]:
    response = supabase_auth(email, password, client)

    if not response.user or not response.session:
        # These fields will be `None` if authentications fails
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    return {
        "message": "Login successful",
        "user_id": response.user.id,
        "access_token": response.session.access_token
    }

@app.get("/")
async def root(request: Request):
    # Landing page
    return templates.TemplateResponse("index.html", {"request": request})
