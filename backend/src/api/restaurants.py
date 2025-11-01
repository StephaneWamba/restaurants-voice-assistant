"""
Restaurant management API endpoints.

Provides REST endpoints for creating and managing restaurants,
including automatic phone number assignment.
"""
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from src.models.restaurants import CreateRestaurantRequest, RestaurantResponse
from src.services.restaurant_service import create_restaurant as create_restaurant_service
from src.services.auth import verify_vapi_secret
from src.middleware.request_id import get_request_id
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


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

    try:
        restaurant_data = create_restaurant_service(
            name=request.name,
            api_key=request.api_key,
            assign_phone=request.assign_phone,
            force_twilio=request.force_twilio
        )

        return RestaurantResponse(
            id=restaurant_data["id"],
            name=restaurant_data["name"],
            api_key=restaurant_data["api_key"],
            phone_number=restaurant_data["phone_number"],
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
