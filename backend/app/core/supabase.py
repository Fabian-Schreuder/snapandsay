from functools import lru_cache
from supabase import create_client, Client
from app.config import settings

@lru_cache()
def get_supabase_client() -> Client:
    """
    Get or create a Supabase client.
    Cached to reuse the connection.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
