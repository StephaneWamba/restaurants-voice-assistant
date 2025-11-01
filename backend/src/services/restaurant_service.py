"""Service for restaurant management."""
from typing import Optional, Dict, Any
from uuid import uuid4
from src.services.supabase_client import get_supabase_service_client
from src.services.phone_service import assign_phone_to_restaurant
import logging

logger = logging.getLogger(__name__)


def create_restaurant(
    name: str,
    api_key: Optional[str] = None,
    assign_phone: bool = True,
    force_twilio: bool = False
) -> Dict[str, Any]:
    """
    Create a new restaurant.

    Args:
        name: Restaurant name
        api_key: Optional custom API key (auto-generated if not provided)
        assign_phone: Whether to automatically assign phone number
        force_twilio: Force Twilio phone creation (skip existing phones)

    Returns:
        Dictionary with restaurant data including phone_number if assigned

    Raises:
        Exception: If restaurant creation fails
    """
    supabase = get_supabase_service_client()

    final_api_key = api_key or f"api_key_{uuid4().hex[:16]}"

    result = supabase.table("restaurants").insert({
        "name": name,
        "api_key": final_api_key
    }).execute()

    if not result.data:
        raise Exception("Failed to create restaurant")

    restaurant_data = result.data[0]
    restaurant_id = restaurant_data["id"]
    phone_number = None

    if assign_phone:
        try:
            phone_number = assign_phone_to_restaurant(
                restaurant_id, force_twilio=force_twilio)
        except Exception as e:
            logger.warning(
                f"Failed to assign phone number to restaurant {restaurant_id}: {e}")

    return {
        "id": restaurant_id,
        "name": restaurant_data["name"],
        "api_key": restaurant_data["api_key"],
        "phone_number": phone_number,
        "created_at": restaurant_data["created_at"]
    }

