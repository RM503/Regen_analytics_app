from supabase import Client
from gotrue.types import AuthResponse
import logging 

logging.basicConfig(level=logging.INFO)

def supabase_auth(
    supabase_auth_email: str,
    supabase_auth_password: str,
    client: Client
) -> AuthResponse | None:
    """
    This function authenticates Supabase logins.
    """
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
