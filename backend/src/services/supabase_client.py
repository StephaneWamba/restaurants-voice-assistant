import os
from supabase import create_client, Client
from src.config import get_settings
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client singleton (uses anon key - for reads and operations allowed by RLS)"""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_service_client() -> Client:
    """Get Supabase client with service role key (bypasses RLS - for writes and admin operations)"""
    settings = get_settings()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key:
        service_key = settings.supabase_anon_key
    return create_client(settings.supabase_url, service_key)
