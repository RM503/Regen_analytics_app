"""
This is the main FastAPI backend that directs users to different
parts of the dashboard
"""
import os
import dotenv
from typing import Annotated
from fastapi import Form, FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode
from flask import Flask
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

# Load environment variables
dotenv.load_dotenv(override=True)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")

# Initialize Supabase client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

shared_flask_server = Flask(__name__)

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
        request: Request,
        email: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)]
    ) -> dict[str, str]:
    """
    This function accepts user login credentials from the
    HTML login form and performs authentication.

    Args: (i) email: user's email
          (ii) password: user's password
    
    Returns: If successfull, it returns user to the landing
             page and stores session information.
    """
    response = supabase_auth(email, password, client)

    if not response or not response.user or not response.session:
        # This will show an unsuccessful login error on the landing page
        # Redirect back to `/` with error message
        query = urlencode({"error": "Invalid email or password."})
        return RedirectResponse(url=f"/?{query}", status_code=302)
    
    # Store session tokens
    request.session["user_id"] = response.user.id
    request.session["access_token"] = response.session.access_token
    
    return RedirectResponse(url="/", status_code=302)

@app.get("/")
async def root(request: Request, error: str=None):
    # Landing page
    return templates.TemplateResponse("index.html", {
        "request": request,
        "error": error
    })
