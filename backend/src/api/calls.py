"""
Call history API endpoints.

Provides REST endpoints for managing voice assistant call records,
including listing call history and creating new call entries.
"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from src.models.calls import CreateCallRequest
from src.services.call_service import list_calls as list_calls_service, create_call as create_call_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/calls",
    summary="List Call History",
    description="List call history for a restaurant, ordered by most recent first.",
    responses={
        200: {
            "description": "Call history retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "call_abc123",
                                "started_at": "2025-01-01T12:00:00Z",
                                "ended_at": "2025-01-01T12:05:00Z",
                                "duration_seconds": 300,
                                "caller": "+1234567890",
                                "outcome": "completed",
                                "messages": []
                            }
                        ]
                    }
                }
            }
        },
        422: {"description": "restaurant_id is required"},
        500: {"description": "Failed to fetch call history"}
    }
)
def list_calls(
    x_restaurant_id: Optional[str] = Header(
        None, alias="X-Restaurant-Id", description="Restaurant UUID (alternative to query param)"),
    restaurant_id_q: Optional[str] = Query(
        None, alias="restaurant_id", description="Restaurant UUID"),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of results")
):
    """
    List call history for a restaurant, ordered by most recent first.

    Supports restaurant_id from header (X-Restaurant-Id) or query parameter.
    """
    restaurant_id = (x_restaurant_id or restaurant_id_q or "").strip()
    if not restaurant_id:
        raise HTTPException(
            status_code=422, detail="restaurant_id is required")

    try:
        calls = list_calls_service(restaurant_id, limit)
        return {"data": calls}
    except Exception as e:
        logger.error(
            f"Error fetching calls for restaurant_id={restaurant_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch call history")


@router.post(
    "/calls",
    summary="Create Call Record",
    description="Create a call history record. Restaurant ID priority: X-Restaurant-Id header > payload.restaurant_id",
    responses={
        200: {
            "description": "Call record created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "id": "call_abc123"
                    }
                }
            }
        },
        422: {"description": "restaurant_id is required"},
        500: {"description": "Failed to create call record"}
    }
)
def create_call(
    payload: CreateCallRequest,
    x_restaurant_id: Optional[str] = Header(
        None, alias="X-Restaurant-Id", description="Restaurant UUID (alternative to payload)"),
):
    """
    Create a call history record.

    Restaurant ID priority: X-Restaurant-Id header > payload.restaurant_id
    Fields: started_at, ended_at, duration_seconds, caller, outcome, messages
    Messages format: [{"role": "user"|"assistant", "content": "text", "timestamp": "ISO string"}]
    """
    restaurant_id = (
        x_restaurant_id or payload.restaurant_id or ""
    ).strip()
    if not restaurant_id:
        raise HTTPException(
            status_code=422, detail="restaurant_id is required")

    try:
        call_id = create_call_service(
            restaurant_id=restaurant_id,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            duration_seconds=payload.duration_seconds,
            caller=payload.caller,
            outcome=payload.outcome,
            messages=payload.messages
        )
        return {"success": True, "id": call_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating call record for restaurant_id={restaurant_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to create call record")
