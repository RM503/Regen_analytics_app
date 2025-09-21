# Flask backend 
import logging
import os 

import dotenv
from flask import (
    Flask, 
    make_response,
    redirect, 
    request, 
    render_template, 
    session, 
    url_for
) 
from supabase import create_client
from werkzeug.wrappers import Response

from config_loader import init_config

init_config() # noqa: E402

from auth.supabase_auth import supabase_auth

from src.initial_market_data.dash0_main import init_dash0
from src.polygon_generator.dash1_main import init_dash1
from src.farmland_characteristics.dash2_main import init_dash2
from src.farmland_statistics.dash3_main import init_dash3

from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Load environment variables
#dotenv.load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

# Initialize Supabase client
try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logging.warning(f"Failed to create Supabase client: {e}")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SESSION_SECRET_KEY

@app.route("/login", methods=["POST"])
def login() -> Response:
    """
    This function accepts user login credentials from the
    HTML login form and performs authentication.
    """
    email =  request.form.get("email")
    password = request.form.get("password")
    response = supabase_auth(email, password, client)

    # Check for incorrect login
    if not response or not response.user or not response.session:
        session["login_error"] = "Invalid email or password."
        return redirect(url_for("root"))
    
    # Store session tokens
    session["user_name"] = email.split("@")[0]
    session["user_id"] = response.user.id 
    session["access_token"] = response.session.access_token
    session["login_success"] = "Login successful!"
    
    r = make_response(redirect(url_for("root")))
    r.set_cookie("access_token", response.session.access_token, httponly=True)
    return r

@app.route("/logout", methods=["POST"])
def logout() -> Response:
    """
    This function clears session keys and logs the user out.
    """
    session.clear() 
    session["login_success"] = "You have been logged out!"

    return redirect(url_for("root"))
    
@app.route("/", methods=["GET"])
def root():
    # Landing page
    success = session.pop("login_success", None)
    error = session.pop("login_error", None)
    token = session.get("access_token", None)
    username = session.get("user_name", None)

    return render_template(
        "index.html",
        success=success,
        error=error,
        token=token,
        username=username
    )

# Initialize Dash apps
init_dash0(app)
init_dash1(app)
init_dash2(app)
init_dash3(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)