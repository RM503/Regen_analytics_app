import os 

from supabase import Client, create_client

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_service_client = None 

def get_service_supabase_client() -> Client:
    """
    Returns a Supabase client using the SERVICE ROLE key.
    Intended ONLY for backend / worker use.
    """
    global _service_client

    if _service_client is None:
        _service_client = create_client(
            _SUPABASE_URL,
            _SUPABASE_SERVICE_KEY,
        )

    return _service_client