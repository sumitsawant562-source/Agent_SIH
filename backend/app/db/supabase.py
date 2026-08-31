from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns the standard Supabase client initialized with anon key.
    Returns None if SUPABASE_URL or SUPABASE_ANON_KEY are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            return _supabase_client
        except Exception as e:
            print(f"[Supabase Init Error] Could not initialize Supabase client: {e}")
            return None
    return None


def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns the Supabase service-role client for backend administrative actions.
    Falls back to anon key client if service role key is not provided.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if settings.SUPABASE_URL and key:
        try:
            _supabase_admin_client = create_client(settings.SUPABASE_URL, key)
            return _supabase_admin_client
        except Exception as e:
            print(f"[Supabase Admin Init Error] Could not initialize Supabase admin client: {e}")
            return None
    return None
