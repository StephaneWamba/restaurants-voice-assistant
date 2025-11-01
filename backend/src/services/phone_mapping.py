"""
Phone number to restaurant_id mapping service.

Stores and retrieves phone number → restaurant_id mappings for routing calls
to the correct restaurant when using a shared assistant.
"""
from src.services.supabase_client import get_supabase_service_client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_restaurant_id_from_phone(phone_number: str) -> Optional[str]:
    """
    Get restaurant_id for a phone number.

    Args:
        phone_number: Phone number in any format (e.g., "+19308889330", "+1 (930) 888 9330")

    Returns:
        restaurant_id if mapping exists, None otherwise
    """
    if not phone_number or not isinstance(phone_number, str):
        return None

    supabase = get_supabase_service_client()

    phone_clean = phone_number.replace(" ", "").replace(
        "(", "").replace(")", "").replace("-", "")

    try:
        resp = supabase.table("restaurant_phone_mappings").select(
            "restaurant_id"
        ).eq("phone_number", phone_clean).limit(1).execute()

        if resp.data:
            return resp.data[0].get("restaurant_id")
    except Exception as e:
        logger.warning(f"Error fetching phone mapping: {e}")
        return None

    return None


def create_phone_mapping(phone_number: str, restaurant_id: str) -> bool:
    """
    Create or update phone number → restaurant_id mapping.

    Args:
        phone_number: Phone number in E.164 format (e.g., "+19308889330")
        restaurant_id: Restaurant UUID

    Returns:
        True if successful, False otherwise
    """
    if not phone_number or not restaurant_id:
        return False

    supabase = get_supabase_service_client()

    phone_clean = phone_number.replace(" ", "").replace(
        "(", "").replace(")", "").replace("-", "")

    try:
        supabase.table("restaurant_phone_mappings").upsert({
            "phone_number": phone_clean,
            "restaurant_id": restaurant_id
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Error creating phone mapping: {e}", exc_info=True)
        return False
