"""
Vapi API client wrapper.

Handles HTTP requests to Vapi API with error handling.
"""

import requests
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VapiAPIError(Exception):
    """Exception raised for Vapi API errors."""
    pass


class VapiClient:
    """
    Client for interacting with Vapi API.

    Provides methods for creating, listing, and deleting tools and assistants.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.vapi.ai"):
        """
        Initialize Vapi client.

        Args:
            api_key: Vapi API key
            base_url: Vapi API base URL (default: https://api.vapi.ai)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make HTTP request.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., "/tool" or "/assistant")
            json_data: Optional JSON payload

        Returns:
            Response object

        Raises:
            VapiAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
                timeout=30
            )
            return response
        except requests.exceptions.RequestException as e:
            raise VapiAPIError(f"API request failed: {e}") from e

    def create_tool(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a function tool in Vapi.

        Args:
            tool_config: Tool configuration dictionary

        Returns:
            Created tool data including ID

        Raises:
            VapiAPIError: If tool creation fails
        """
        response = self._request("POST", "/tool", json_data=tool_config)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to create tool: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def create_assistant(self, assistant_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an assistant in Vapi.

        Args:
            assistant_config: Assistant configuration dictionary

        Returns:
            Created assistant data including ID

        Raises:
            VapiAPIError: If assistant creation fails
        """
        import copy

        config_copy = copy.deepcopy(assistant_config)

        def remove_voice_recursive(obj):
            if isinstance(obj, dict):
                obj.pop("voice", None)
                obj.pop("voice_id", None)
                for value in list(obj.values()):
                    remove_voice_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_voice_recursive(item)

        remove_voice_recursive(config_copy)
        response = self._request("POST", "/assistant",
                                 json_data=config_copy)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to create assistant: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def update_assistant(self, assistant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an assistant in Vapi.

        Args:
            assistant_id: Assistant ID to update
            updates: Dictionary of fields to update (e.g., {"serverUrl": "https://..."})

        Returns:
            Updated assistant data

        Raises:
            VapiAPIError: If update fails
        """
        import copy

        updates_copy = copy.deepcopy(updates)

        def remove_voice_recursive(obj):
            if isinstance(obj, dict):
                obj.pop("voice", None)
                obj.pop("voice_id", None)
                for value in list(obj.values()):
                    remove_voice_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_voice_recursive(item)

        remove_voice_recursive(updates_copy)
        response = self._request(
            "PATCH", f"/assistant/{assistant_id}", json_data=updates_copy)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to update assistant: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all tools.

        Returns:
            List of tool dictionaries

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", "/tool")

        if response.status_code != 200:
            error_msg = f"Failed to list tools: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        tools = response.json()
        return tools if isinstance(tools, list) else []

    def list_assistants(self) -> List[Dict[str, Any]]:
        """
        List all assistants.

        Returns:
            List of assistant dictionaries

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", "/assistant")

        if response.status_code != 200:
            error_msg = f"Failed to list assistants: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        assistants = response.json()
        return assistants if isinstance(assistants, list) else []

    def delete_tool(self, tool_id: str) -> bool:
        """
        Delete a tool by ID.

        Args:
            tool_id: Tool ID to delete

        Returns:
            True if successful, False otherwise
        """
        response = self._request("DELETE", f"/tool/{tool_id}")

        return response.status_code in [200, 204]

    def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant by ID.

        Args:
            assistant_id: Assistant ID to delete

        Returns:
            True if successful, False otherwise
        """
        response = self._request("DELETE", f"/assistant/{assistant_id}")

        return response.status_code in [200, 204]

    def get_phone_number(self, phone_number_id: str) -> Dict[str, Any]:
        """
        Get a single phone number by ID.

        Args:
            phone_number_id: Phone number ID

        Returns:
            Phone number data

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", f"/phone-number/{phone_number_id}")

        if response.status_code != 200:
            error_msg = f"Failed to get phone number: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def list_phone_numbers(self) -> List[Dict[str, Any]]:
        """
        List all available phone numbers.

        Returns:
            List of phone number dictionaries

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", "/phone-number")

        if response.status_code != 200:
            error_msg = f"Failed to list phone numbers: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        phone_numbers = response.json()
        return phone_numbers if isinstance(phone_numbers, list) else []

    def create_phone_number(self, phone_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a phone number via Vapi API.

        For automatic phone number provisioning:
        - Twilio: Use provider="twilio" with twilioAccountSid
        - Other providers: Use provider="vonage", "telnyx" with credentials
        - BYO numbers: Use provider="byo-phone-number" with number and credentialId

        For free Vapi test numbers: Must be created via Dashboard (not API).

        Args:
            phone_config: Configuration dict with:
                - provider: "twilio", "vonage", "telnyx", "vapi", or "byo-phone-number"
                - twilioAccountSid: Required if provider="twilio" (auto-provisions numbers)
                - number: Phone number in E.164 format (if using existing number)
                - credentialId: Required if provider="byo-phone-number"

        Returns:
            Created phone number data

        Raises:
            VapiAPIError: If creation fails
        """
        config = phone_config or {}
        response = self._request("POST", "/phone-number", json_data=config)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to create phone number: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def create_credential(self, credential_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a credential in Vapi.

        Args:
            credential_config: Credential configuration dict with:
                - provider: "twilio", "vonage", "telnyx", etc.
                - name: Optional name for the credential
                - accountSid: Required for provider="twilio" (Twilio Account SID)
                - authToken: Required for provider="twilio" (Twilio Auth Token)
                - apiKey: Also required for provider="twilio" (same as accountSid)
                - apiSecret: Also required for provider="twilio" (same as authToken)
                - (other provider-specific fields)

        Returns:
            Created credential data including ID

        Raises:
            VapiAPIError: If credential creation fails
        """
        response = self._request(
            "POST", "/credential", json_data=credential_config)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to create credential: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def list_credentials(self) -> List[Dict[str, Any]]:
        """
        List all credentials.

        Returns:
            List of credential dictionaries

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", "/credential")

        if response.status_code != 200:
            error_msg = f"Failed to list credentials: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        credentials = response.json()
        return credentials if isinstance(credentials, list) else []

    def get_credential(self, credential_id: str) -> Dict[str, Any]:
        """
        Get a single credential by ID.

        Args:
            credential_id: Credential ID

        Returns:
            Credential data

        Raises:
            VapiAPIError: If request fails
        """
        response = self._request("GET", f"/credential/{credential_id}")

        if response.status_code != 200:
            error_msg = f"Failed to get credential: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def update_phone_number(self, phone_number_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a phone number.

        Args:
            phone_number_id: Phone number ID to update
            updates: Dictionary of fields to update (e.g., {"assistantId": "asst_123"})

        Returns:
            Updated phone number data

        Raises:
            VapiAPIError: If update fails
        """
        response = self._request(
            "PATCH", f"/phone-number/{phone_number_id}", json_data=updates)

        if response.status_code not in [200, 201]:
            error_msg = f"Failed to update phone number: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return response.json()

    def delete_phone_number(self, phone_number_id: str) -> bool:
        """
        Delete a phone number by ID.

        Args:
            phone_number_id: Phone number ID to delete

        Returns:
            True if successful, False otherwise

        Raises:
            VapiAPIError: If deletion fails
        """
        response = self._request("DELETE", f"/phone-number/{phone_number_id}")

        if response.status_code not in [200, 204]:
            error_msg = f"Failed to delete phone number: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"

            logger.error(error_msg)
            raise VapiAPIError(error_msg)

        return True
