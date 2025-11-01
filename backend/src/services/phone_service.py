"""Service for phone number assignment to restaurants."""
from typing import Optional
import os
import logging
from vapi.manager import VapiResourceManager
from src.services.phone_mapping import create_phone_mapping, get_restaurant_id_from_phone
from src.services.twilio_service import create_and_assign_twilio_phone

logger = logging.getLogger(__name__)


def assign_phone_to_restaurant(restaurant_id: str, force_twilio: bool = False) -> Optional[str]:
    """
    Assign a phone number to a restaurant.

    If force_twilio=True, skips existing phones and directly creates a Twilio number.
    Otherwise, first tries to assign an existing unassigned phone number.
    If none available, attempts to create a new Twilio phone number.

    Args:
        restaurant_id: Restaurant ID to assign phone to
        force_twilio: If True, skip existing phones and force Twilio creation

    Returns phone number if successful, None otherwise.
    """
    api_key = os.environ.get("VAPI_API_KEY")
    backend_url = os.environ.get("PUBLIC_BACKEND_URL")

    if not api_key or not backend_url:
        return None

    try:
        manager = VapiResourceManager(api_key=api_key, backend_url=backend_url)

        assistants = manager.client.list_assistants()
        existing_assistant = next(
            (a for a in assistants if a.get("name")
             == "Restaurant Voice Assistant"),
            None
        )

        if not existing_assistant:
            logger.warning("No shared assistant found for phone assignment")
            return None

        assistant_id = existing_assistant.get("id")

        # Skip existing phones if force_twilio is True
        if not force_twilio:
            # Try to assign existing unassigned phone number
            phone_numbers = manager.client.list_phone_numbers()
            if phone_numbers:
                available_phone = None
                available_phone_id = None

                for pn in phone_numbers:
                    pn_assistant_id = pn.get("assistantId")
                    pn_number = pn.get("number")

                    if not pn_number:
                        continue

                    if not pn_assistant_id or pn_assistant_id == assistant_id:
                        existing_restaurant = get_restaurant_id_from_phone(
                            pn_number)
                        if not existing_restaurant:
                            available_phone = pn_number
                            available_phone_id = pn.get("id")
                            break

                if not available_phone:
                    for pn in phone_numbers:
                        pn_number = pn.get("number")
                        if pn_number:
                            existing_restaurant = get_restaurant_id_from_phone(
                                pn_number)
                            if not existing_restaurant:
                                available_phone = pn_number
                                available_phone_id = pn.get("id")
                                break

                if available_phone and available_phone_id:
                    manager.client.update_phone_number(
                        available_phone_id, {"assistantId": assistant_id}
                    )

                    if create_phone_mapping(available_phone, restaurant_id):
                        return available_phone

        # If force_twilio or no existing phone available, try to create Twilio phone
        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

        if twilio_account_sid and twilio_auth_token:
            logger.info(
                f"Attempting to create Twilio phone for restaurant {restaurant_id}")
            return create_and_assign_twilio_phone(
                restaurant_id=restaurant_id,
                assistant_id=assistant_id,
                client=manager.client,
                manager=manager,
                twilio_account_sid=twilio_account_sid,
                twilio_auth_token=twilio_auth_token
            )
        else:
            logger.warning(
                "No phone numbers available and Twilio credentials not configured"
            )

        return None

    except Exception as e:
        logger.error(f"Error assigning phone number: {e}", exc_info=True)
        return None
