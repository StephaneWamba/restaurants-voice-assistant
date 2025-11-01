"""
Resource manager for Vapi tools and assistants.

Provides high-level operations for managing Vapi resources using configuration files.
"""

from typing import Dict, Any, List, Optional
import logging
from .client import VapiClient, VapiAPIError
from .config_loader import load_config, validate_config

logger = logging.getLogger(__name__)


class VapiResourceManager:
    """
    Manager for Vapi resources (tools and assistants).

    Handles creation, listing, and deletion of tools and assistants
    based on YAML configuration files.
    """

    def __init__(
        self,
        api_key: str,
        backend_url: str,
        base_url: str = "https://api.vapi.ai"
    ):
        """
        Initialize resource manager.

        Args:
            api_key: Vapi API key
            backend_url: Public URL of the backend API
            base_url: Vapi API base URL (default: https://api.vapi.ai)
        """
        self.client = VapiClient(api_key, base_url)
        self.backend_url = backend_url.rstrip("/")
        self.config = None

    def load_and_validate_config(self) -> Dict[str, Any]:
        """Load and validate configuration files."""
        self.config = load_config()
        validate_config(self.config, self.backend_url)
        return self.config

    def build_tool_config(self, tool_def: Dict[str, Any], for_assistant: bool = False) -> Dict[str, Any]:
        """
        Build Vapi tool configuration from YAML definition.

        Args:
            tool_def: Tool definition from tools.yaml
            for_assistant: If True, includes messages for assistant format

        Returns:
            Tool configuration for Vapi API
        """
        server_url = f"{self.backend_url}/api/vapi/knowledge-base"

        server_config = {
            "url": server_url,
            "secret": self.client.api_key
        }

        tool_config = {
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"]
            },
            "server": server_config
        }

        if for_assistant:
            tool_messages = self.config["prompts"].get("tool_messages", {})
            request_start = tool_messages.get(
                "request_start", "Let me check that for you.")
            tool_config["messages"] = [
                {"type": "request-start", "content": request_start}]

        return tool_config

    def create_tools(self) -> Dict[str, str]:
        """Create all tools from configuration."""
        if not self.config:
            raise ValueError(
                "Configuration not loaded. Call load_and_validate_config() first.")

        tool_map = {}
        for tool_def in self.config["tools"]:
            tool_config = self.build_tool_config(tool_def, for_assistant=False)
            tool_data = self.client.create_tool(tool_config)
            if tool_id := tool_data.get("id"):
                tool_map[tool_def["name"]] = tool_id
        return tool_map

    def create_assistant(self, tool_name_to_id: Dict[str, str]) -> str:
        """Create assistant with tools from configuration."""
        if not self.config:
            raise ValueError(
                "Configuration not loaded. Call load_and_validate_config() first.")

        tools_block = [
            self.build_tool_config(tool_def, for_assistant=True)
            for tool_def in self.config["tools"]
            if tool_def["name"] in tool_name_to_id
        ]
        if not tools_block:
            raise ValueError("No valid tools to attach to assistant")

        assistant_config = self.config["assistant"].copy()
        assistant_config.pop("voice", None)

        system_prompt = self.config["prompts"]["system_prompt"]

        model_config = assistant_config.get("model", {}).copy()
        model_config["messages"] = [
            {"role": "system", "content": system_prompt}]
        model_config["tools"] = tools_block

        assistant_config.update({
            "model": model_config,
            "firstMessage": self.config["prompts"]["first_message"],
            "serverUrl": f"{self.backend_url}/api/vapi/assistant-request",
            "serverUrlSecret": self.client.api_key
        })

        assistant_id = self.client.create_assistant(assistant_config).get("id")
        if not assistant_id:
            raise VapiAPIError("Assistant creation returned no ID")
        return assistant_id

    def assign_phone_number(
        self,
        assistant_id: str,
        phone_number_id: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign a phone number to an assistant.

        Args:
            assistant_id: Assistant ID
            phone_number_id: Optional phone number ID. If provided, assigns directly.
            phone_number: Optional phone number string (e.g., "+19308889330"). 
                If provided, will search for matching number and assign it.

        Returns:
            Phone number ID if successful, None otherwise

        Raises:
            VapiAPIError: If assignment fails
        """
        if phone_number_id:
            self.client.update_phone_number(
                phone_number_id, {"assistantId": assistant_id})
            return phone_number_id

        try:
            phone_numbers = self.client.list_phone_numbers()

            if phone_number:
                target_clean = phone_number.replace(" ", "").replace(
                    "(", "").replace(")", "").replace("-", "")
                for pn in phone_numbers:
                    number = pn.get("number", "")
                    number_clean = number.replace(" ", "").replace(
                        "(", "").replace(")", "").replace("-", "")
                    if target_clean in number_clean or number_clean in target_clean:
                        found_id = pn.get("id")
                        if found_id:
                            self.client.update_phone_number(
                                found_id, {"assistantId": assistant_id})
                            return found_id

            if phone_numbers:
                first_available = phone_numbers[0].get("id")
                if first_available:
                    self.client.update_phone_number(
                        first_available, {"assistantId": assistant_id})
                    return first_available
        except Exception as e:
            logger.warning(f"Could not assign phone number: {e}")
            return None

        return None

    def list_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all existing tools and assistants.

        Returns:
            Dictionary with 'tools' and 'assistants' keys
        """
        return {
            "tools": self.client.list_tools(),
            "assistants": self.client.list_assistants()
        }

    def cleanup_all_resources(self) -> Dict[str, int]:
        """Delete all existing tools and assistants."""
        try:
            resources = self.list_resources()
        except Exception as e:
            logger.warning(f"Could not list resources for cleanup: {e}")
            return {"assistants": 0, "tools": 0}

        deleted_assistants = 0
        deleted_tools = 0

        for a in resources.get("assistants", []):
            if a.get("id"):
                try:
                    self.client.delete_assistant(a["id"])
                    deleted_assistants += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to delete assistant {a.get('id')}: {e}")

        for t in resources.get("tools", []):
            if t.get("id"):
                try:
                    self.client.delete_tool(t["id"])
                    deleted_tools += 1
                except Exception as e:
                    logger.warning(f"Failed to delete tool {t.get('id')}: {e}")

        return {
            "assistants": deleted_assistants,
            "tools": deleted_tools
        }
