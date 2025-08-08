# Flask backend test (check if access token can be passed to dash apps)
import os 
import dotenv
from flask import Flask, redirect, request, render_template, session, url_for 
from werkzeug.wrappers import Response
from supabase import create_client
from auth.supabase_auth import supabase_auth

# Load environment variables
dotenv.load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

# Initialize Supabase client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
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
    session["user_id"] = response.user.id 
    session["access_token"] = response.session.access_token
    session["login_success"] = "Login successful!"
    
    return redirect(f"/?token={response.session.access_token}")

@app.route("/logout", methods=["POST"])
def logout() -> Response:
    session.clear() # clears all session keys
    session["login_success"] = "You have been logged out!"

    return redirect("/")
    
@app.route("/", methods=["GET"])
def root():
    # Landing page
    success = session.pop("login_success", None)
    error = session.pop("login_error", None)
    token = session.get("access_token", None)

    return render_template(
        "index.html",
        success=success,
        error=error,
        token=token
    )

if __name__ == "__main__":
    app.run(debug=True)