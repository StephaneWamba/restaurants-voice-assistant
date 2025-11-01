"""Health check endpoint with service connectivity checks."""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import asyncio
from src.services.supabase_client import get_supabase_service_client
from src.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

settings = get_settings()


async def check_supabase() -> dict:
    """Check Supabase connectivity."""
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


async def check_openai() -> dict:
    """Check OpenAI API connectivity."""
    try:
        import openai
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        start = datetime.utcnow()
        response = client.models.list(timeout=5.0)
        latency = (datetime.utcnow() - start).total_seconds() * 1000

        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_vapi() -> dict:
    """Check Vapi API connectivity."""
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


@router.get(
    "/health",
    summary="Health Check",
    description="Health check endpoint with service connectivity checks. Returns detailed status of all dependencies."
)
async def health_check():
    """
    Health check endpoint with service connectivity checks.

    Checks connectivity to:
    - Supabase (database)
    - OpenAI (embeddings API)
    - Vapi (voice assistant platform)

    Returns 200 if all critical services are healthy, 503 if any are unhealthy.
    """
    checks = await asyncio.gather(
        check_supabase(),
        check_openai(),
        check_vapi(),
        return_exceptions=True
    )

    supabase_status = checks[0] if not isinstance(checks[0], Exception) else {
        "status": "error", "error": str(checks[0])}
    openai_status = checks[1] if not isinstance(checks[1], Exception) else {
        "status": "error", "error": str(checks[1])}
    vapi_status = checks[2] if not isinstance(checks[2], Exception) else {
        "status": "error", "error": str(checks[2])}

    all_healthy = (
        supabase_status.get("status") == "healthy" and
        openai_status.get("status") == "healthy"
    )

    overall_status = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "restaurant-voice-assistant",
        "checks": {
            "supabase": supabase_status,
            "openai": openai_status,
            "vapi": vapi_status
        }
    }

    if not all_healthy:
        raise HTTPException(status_code=503, detail=overall_status)

    return overall_status
