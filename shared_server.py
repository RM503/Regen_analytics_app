import os 
import dotenv
from flask import Flask, g, session, request

dotenv.load_dotenv(override=True)

shared_flask_server = Flask(__name__)
shared_flask_server.secret_key = os.environ.get("SESSION_SECRET_KEY")

@shared_flask_server.before_request
def load_supabase_token():
    # Try to get token from different sources
    access_token = None
    user_id = None
    
    # First try session (for same-domain requests)
    access_token = session.get("access_token")
    user_id = session.get("user_id")
    
    # Then try query parameters (for direct links with token)
    if not access_token and request.args.get("token"):
        access_token = request.args.get("token")
    
    # Then try custom header (set by middleware)
    if not access_token and request.headers.get("X-Access-Token"):
        access_token = request.headers.get("X-Access-Token")
    
    # Store in Flask g object for use in app callbacks
    g.access_token = access_token
    g.user_id = user_id

def get_current_token():
    """Helper function to get current access token from Flask g"""
    return getattr(g, 'access_token', None)

def get_current_user_id():
    """Helper function to get current user ID from Flask g"""
    return getattr(g, 'user_id', None)
