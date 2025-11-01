"""Service for health check operations."""
from typing import Dict
from datetime import datetime
from src.services.supabase_client import get_supabase_service_client
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_supabase() -> Dict:
    """Check Supabase connectivity and measure latency."""
    try:
        from datetime import datetime as dt
        supabase = get_supabase_service_client()
        start = dt.utcnow()
        result = supabase.table("restaurants").select("id").limit(1).execute()
        latency = (dt.utcnow() - start).total_seconds() * 1000
        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_openai() -> Dict:
    """Check OpenAI API connectivity and measure latency."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        start = datetime.utcnow()
        response = client.models.list(timeout=5.0)
        latency = (datetime.utcnow() - start).total_seconds() * 1000

        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_vapi() -> Dict:
    """Check Vapi API connectivity and measure latency."""
    try:
        import os
        from vapi.client import VapiClient

        api_key = os.environ.get("VAPI_API_KEY")
        if not api_key:
            return {"status": "not_configured"}

        client = VapiClient(api_key=api_key)
        start = datetime.utcnow()
        assistants = client.list_assistants()
        latency = (datetime.utcnow() - start).total_seconds() * 1000

        return {"status": "healthy", "latency_ms": round(latency, 2), "assistants": len(assistants)}
    except Exception as e:
        logger.error(f"Vapi health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
