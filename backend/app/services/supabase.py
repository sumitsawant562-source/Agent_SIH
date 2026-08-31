"""
Supabase client service layer helpers.
Re-exports client accessors from app.db.supabase for consistent architecture.
"""

from typing import Optional
from supabase import Client
from app.db.supabase import get_supabase_client, get_supabase_admin_client

__all__ = ["get_supabase_client", "get_supabase_admin_client", "Client"]
