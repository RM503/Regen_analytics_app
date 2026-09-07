from __future__ import annotations

import os

from dotenv import load_dotenv
from gotrue.errors import AuthApiError
from gotrue.types import AuthResponse
from pydantic import BaseModel, EmailStr, ValidationError, field_validator
from supabase import Client

from utils.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class SupabaseCredentials(BaseModel):
    """
    Pydantic model for validating Supabase credentials.
    Defines a method that checks for empty password strings.
    """
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password string cannot be empty")
        return v


def supabase_auth(
    supabase_auth_email: str,
    supabase_auth_password: str,
    client: Client
) -> AuthResponse:
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
        credentials = SupabaseCredentials(
            email=supabase_auth_email,
            password=supabase_auth_password
        )
    except ValidationError as e:
        logger.error(f"Invalid credentials: {e}")
        raise

    try:
        # Authentication response
        response = client.auth.sign_in_with_password(
            {
                "email": credentials.email,
                "password": credentials.password
            }
        )
        logger.info(f"User signed in successfully: {response.user.email}")

        return response
    except AuthApiError:
        logger.warning(f"Authentication failed for {credentials.email}")
        raise
    except Exception:
        logger.error(f"An unexpected error occurred for {credentials.email}")
        raise
