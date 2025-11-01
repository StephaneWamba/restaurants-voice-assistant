"""Health check endpoint with service connectivity checks."""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import asyncio
from src.services.health_service import check_supabase, check_openai, check_vapi

router = APIRouter()
logger = logging.getLogger(__name__)


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
