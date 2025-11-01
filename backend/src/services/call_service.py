"""Service for call history management."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.services.supabase_client import get_supabase_client, get_supabase_service_client
import logging

logger = logging.getLogger(__name__)


def list_calls(restaurant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List call history for a restaurant.

    Args:
        restaurant_id: Restaurant UUID
        limit: Maximum number of results

    Returns:
        List of call records
    """
    supabase = get_supabase_client()

    try:
        resp = supabase.table("call_history").select(
            "id, started_at, ended_at, duration_seconds, caller, outcome, messages"
        ).eq("restaurant_id", restaurant_id).order("started_at", desc=True).limit(limit).execute()

        return resp.data or []
    except Exception as e:
        logger.error(
            f"Error fetching calls for restaurant_id={restaurant_id}: {e}", exc_info=True)
        raise


def create_call(
    restaurant_id: str,
    started_at: datetime,
    ended_at: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    caller: Optional[str] = None,
    outcome: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a call history record.

    Args:
        restaurant_id: Restaurant UUID
        started_at: Call start time
        ended_at: Call end time (optional)
        duration_seconds: Call duration in seconds (optional)
        caller: Caller phone number (optional)
        outcome: Call outcome (optional)
        messages: Call messages/transcript (optional)

    Returns:
        Call record ID
    """
    record = {
        "restaurant_id": restaurant_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        "caller": caller,
        "outcome": outcome,
        "messages": messages or [],
    }

    supabase = get_supabase_service_client()
    try:
        resp = supabase.table("call_history").insert(record).execute()

        if not resp.data:
            raise Exception("Failed to create call record")

        return resp.data[0].get("id")
    except Exception as e:
        logger.error(
            f"Error creating call record for restaurant_id={restaurant_id}: {e}", exc_info=True)
        raise

