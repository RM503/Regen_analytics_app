# Supabase Python SDK scripts for authentication

import os 
import dotenv
from pydantic import BaseModel, EmailStr, ValidationError
from flask import session
from supabase import Client, create_client
from gotrue.types import AuthResponse
import logging 

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseCredentials(BaseModel):
    email: EmailStr # Must be an email string 
    password: str

def supabase_auth(
    supabase_auth_email: str,
    supabase_auth_password: str,
    client: Client
) -> AuthResponse | None:
    """
    This function authenticates Supabase logins by first performing
    a validation check on the entered types and then a user
    authentication.

    Args: (i) supabase_auth_email: user's email
          (ii) supabase_auth_password: user's password
          (iii) client: Supabase client
    
    Returns: AuthResponse or None
    """
    try:
        # Validate credentials
        _ = SupabaseCredentials(
            email=supabase_auth_email,
            password=supabase_auth_password
        )
    except ValidationError as e:
        logging.error(f"Invalid credentials: {e}")

        return None

    try:
        # Authentication response
        response = client.auth.sign_in_with_password(
            {
                "email": supabase_auth_email,
                "password": supabase_auth_password
            }
        )
        logging.info(f"User signed in successfully: {response.user.email}")

        return response
    except Exception as e:
        logging.error(f"Error signing in user: {e}")

        return None
    
def get_supabase_client() -> Client | None:
    """
    Create Supabase client with authentication token. 
    The client will only be invoked for performing `INSERT`
    operations from authenticated users.
    """
    token = session.get("access_token")

    if not token:
        return None
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Attach token for RLS authorization
    client.postgrest.auth(token)
    return client