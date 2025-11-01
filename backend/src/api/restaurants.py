"""
Restaurant management API endpoints.

Provides REST endpoints for creating and managing restaurants,
including automatic phone number assignment.
"""
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from src.models.restaurants import CreateRestaurantRequest, RestaurantResponse
from src.services.supabase_client import get_supabase_service_client
from src.services.phone_service import assign_phone_to_restaurant
from src.config import get_settings
from src.services.auth import verify_vapi_secret
from src.middleware.request_id import get_request_id
import logging
from uuid import uuid4

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post(
    "/restaurants",
    response_model=RestaurantResponse,
    responses={
        401: {"description": "Invalid authentication"},
        500: {"description": "Failed to create restaurant"}
    },
    summary="Create Restaurant",
    description="Create a new restaurant with optional automatic phone number assignment."
)
def create_restaurant(
    request: CreateRestaurantRequest,
    http_request: Request,
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret for authentication")
):
    """
    Create a new restaurant.

    Automatically assigns a phone number if assign_phone=True (default).
    - By default, tries existing unassigned phones first, then creates Twilio if needed.
    - Set force_twilio=True to skip existing phones and directly create a Twilio number.

    Phone creation succeeds if:
    - VAPI_API_KEY and PUBLIC_BACKEND_URL are configured
    - TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are configured (for new numbers)
    - Shared assistant exists
    - Twilio account has available numbers/quota

    Returns restaurant data including phone number if assigned.
    """
    verify_vapi_secret(x_vapi_secret)

    supabase = get_supabase_service_client()

    api_key = request.api_key or f"api_key_{uuid4().hex[:16]}"

    try:
        result = supabase.table("restaurants").insert({
            "name": request.name,
            "api_key": api_key
        }).execute()

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create restaurant")

        restaurant_data = result.data[0]
        restaurant_id = restaurant_data["id"]
        phone_number = None

        if request.assign_phone:
            try:
                phone_number = assign_phone_to_restaurant(
                    restaurant_id, force_twilio=request.force_twilio)
            except Exception as e:
                logger.warning(
                    f"Failed to assign phone number to restaurant {restaurant_id}: {e}")

        return RestaurantResponse(
            id=restaurant_id,
            name=restaurant_data["name"],
            api_key=restaurant_data["api_key"],
            phone_number=phone_number,
            created_at=restaurant_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        request_id = get_request_id(http_request)
        logger.error(
            f"Error creating restaurant: {e}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=500, detail="Failed to create restaurant")
