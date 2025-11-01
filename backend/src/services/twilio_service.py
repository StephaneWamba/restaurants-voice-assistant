"""Service for Twilio phone number creation and management."""
from typing import Optional, Dict, Any, List
import os
import logging
import time
import requests
from vapi.client import VapiClient, VapiAPIError
from vapi.manager import VapiResourceManager
from src.services.phone_mapping import create_phone_mapping

logger = logging.getLogger(__name__)


def get_or_create_twilio_credential(
    client: VapiClient,
    twilio_account_sid: str,
    twilio_auth_token: str
) -> Optional[str]:
    """
    Get or create Twilio credential in Vapi.

    Returns credential_id if successful, None otherwise.
    """
    try:
        existing_credentials = client.list_credentials()
        twilio_credential = next(
            (c for c in existing_credentials if c.get("provider") == "twilio"),
            None
        )

        if twilio_credential:
            return twilio_credential.get("id")

        credential_payload = {
            "provider": "twilio",
            "name": "Twilio Credentials",
            "accountSid": twilio_account_sid,
            "authToken": twilio_auth_token,
            "apiKey": twilio_account_sid,
            "apiSecret": twilio_auth_token
        }

        new_credential = client.create_credential(credential_payload)
        return new_credential.get("id")

    except VapiAPIError as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            existing_credentials = client.list_credentials()
            twilio_credential = next(
                (c for c in existing_credentials if c.get("provider") == "twilio"),
                None
            )
            if twilio_credential:
                return twilio_credential.get("id")
        logger.error(f"Failed to create/find Twilio credential: {e}")
        return None
    except Exception as e:
        logger.error(f"Error managing Twilio credential: {e}", exc_info=True)
        return None


def search_twilio_numbers(
    twilio_account_sid: str,
    twilio_auth_token: str,
    country_code: str = "US",
    limit: int = 1
) -> List[Dict[str, Any]]:
    """Search for available Twilio phone numbers."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/AvailablePhoneNumbers/{country_code}/Local.json"
    params = {"Limit": limit}

    try:
        response = requests.get(
            url,
            params=params,
            auth=(twilio_account_sid, twilio_auth_token),
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("available_phone_numbers", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Twilio API error searching numbers: {e}")
        return []


def list_twilio_numbers(
    twilio_account_sid: str,
    twilio_auth_token: str
) -> List[Dict[str, Any]]:
    """List existing Twilio phone numbers."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/IncomingPhoneNumbers.json"
    try:
        response = requests.get(
            url,
            auth=(twilio_account_sid, twilio_auth_token),
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("incoming_phone_numbers", [])
        return []
    except Exception as e:
        logger.error(f"Error listing Twilio numbers: {e}")
        return []


def purchase_twilio_number(
    twilio_account_sid: str,
    twilio_auth_token: str,
    phone_number: str
) -> Dict[str, Any]:
    """Purchase a phone number via Twilio API."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/IncomingPhoneNumbers.json"
    data = {"PhoneNumber": phone_number}

    try:
        response = requests.post(
            url,
            data=data,
            auth=(twilio_account_sid, twilio_auth_token),
            timeout=10
        )
        if response.status_code != 201:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("message", str(error_json))
                error_code = error_json.get("code")
                if error_code == 21404:
                    return {"error": "trial_limit", "message": error_detail}
            except:
                pass
            return {"error": "purchase_failed", "message": error_detail}
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": "request_failed", "message": str(e)}


def create_and_assign_twilio_phone(
    restaurant_id: str,
    assistant_id: str,
    client: VapiClient,
    manager: VapiResourceManager,
    twilio_account_sid: str,
    twilio_auth_token: str
) -> Optional[str]:
    """
    Create a Twilio phone number and assign it to a restaurant.

    Returns phone number if successful, None otherwise.
    """
    try:
        credential_id = get_or_create_twilio_credential(
            client, twilio_account_sid, twilio_auth_token
        )
        if not credential_id:
            logger.warning("Could not get/create Twilio credential")
            return None

        existing_numbers = list_twilio_numbers(
            twilio_account_sid, twilio_auth_token)

        available_numbers = search_twilio_numbers(
            twilio_account_sid, twilio_auth_token, country_code="US", limit=1
        )
        if not available_numbers:
            logger.warning("No available Twilio numbers found")
            if existing_numbers:
                existing_number = existing_numbers[0].get("phone_number")
                if existing_number:
                    phone_number_e164 = existing_number
                else:
                    return None
            else:
                return None
        else:
            phone_number_e164 = available_numbers[0].get("phone_number")
            if not phone_number_e164:
                return None

            already_purchased = any(
                num.get("phone_number") == phone_number_e164
                for num in existing_numbers
            )

            if not already_purchased:
                purchased = purchase_twilio_number(
                    twilio_account_sid, twilio_auth_token, phone_number_e164
                )
                if isinstance(purchased, dict) and purchased.get("error"):
                    error_type = purchased.get("error")
                    if error_type == "trial_limit":
                        logger.warning(
                            "Twilio trial account limit reached. Using existing number if available.")
                        if existing_numbers:
                            existing_number = existing_numbers[0].get(
                                "phone_number")
                            if existing_number:
                                phone_number_e164 = existing_number
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                else:
                    time.sleep(2)

        existing_vapi_numbers = client.list_phone_numbers()
        existing_vapi = next(
            (pn for pn in existing_vapi_numbers if pn.get(
                "number") == phone_number_e164),
            None
        )

        if existing_vapi:
            phone_id = existing_vapi.get("id")
        else:
            phone_config = {
                "provider": "twilio",
                "number": phone_number_e164,
                "twilioAccountSid": twilio_account_sid,
                "twilioAuthToken": twilio_auth_token
            }

            try:
                vapi_phone = client.create_phone_number(phone_config)
                phone_id = vapi_phone.get("id")
                if not phone_id:
                    return None
            except VapiAPIError as e:
                error_msg = str(e).lower()
                if "not found" in error_msg or "number not found" in error_msg:
                    logger.warning("Twilio number not accessible in Vapi")
                return None

        manager.client.update_phone_number(
            phone_id, {"assistantId": assistant_id}
        )

        if create_phone_mapping(phone_number_e164, restaurant_id):
            return phone_number_e164
        else:
            logger.warning(
                f"Failed to save phone mapping for {phone_number_e164}")
            return None

    except Exception as e:
        logger.error(f"Error creating Twilio phone: {e}", exc_info=True)
        return None
