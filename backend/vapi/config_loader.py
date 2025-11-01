"""
Configuration loader for Vapi setup.

Loads and validates YAML configuration files for tools, assistant, and prompts.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Base directory for Vapi config files
CONFIG_DIR = Path(__file__).parent / "config"


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if not isinstance(content, dict):
        raise ValueError(f"Invalid YAML structure in {file_path}")

    return content


def load_config() -> Dict[str, Any]:
    """
    Load all Vapi configuration files.

    Returns:
        Dictionary containing tools, assistant, and prompts configurations

    Raises:
        FileNotFoundError: If any config file is missing
        ValueError: If any config file has invalid structure
    """
    config = {}

    tools_path = CONFIG_DIR / "tools.yaml"
    config["tools"] = load_yaml_file(tools_path).get("tools", [])

    assistant_path = CONFIG_DIR / "assistant.yaml"
    config["assistant"] = load_yaml_file(assistant_path).get("assistant", {})

    prompts_path = CONFIG_DIR / "prompts.yaml"
    config["prompts"] = load_yaml_file(prompts_path).get("prompts", {})

    return config


def validate_config(config: Dict[str, Any], backend_url: Optional[str] = None) -> None:
    """
    Validate configuration structure and required fields.

    Args:
        config: Configuration dictionary from load_config()
        backend_url: Optional backend URL to validate format

    Raises:
        ValueError: If configuration is invalid
    """
    errors = []

    if "tools" not in config:
        errors.append("Missing 'tools' configuration")
    elif not isinstance(config["tools"], list):
        errors.append("'tools' must be a list")
    elif len(config["tools"]) == 0:
        errors.append("At least one tool must be defined")
    else:
        for idx, tool in enumerate(config["tools"]):
            if not isinstance(tool, dict):
                errors.append(f"Tool {idx} must be a dictionary")
                continue

            if "name" not in tool:
                errors.append(f"Tool {idx} is missing 'name'")
            if "description" not in tool:
                errors.append(f"Tool {idx} is missing 'description'")
            if "parameters" not in tool:
                errors.append(f"Tool {idx} is missing 'parameters'")

    if "assistant" not in config:
        errors.append("Missing 'assistant' configuration")
    elif not isinstance(config["assistant"], dict):
        errors.append("'assistant' must be a dictionary")
    else:
        if "name" not in config["assistant"]:
            errors.append("Assistant configuration missing 'name'")
        if "model" not in config["assistant"]:
            errors.append("Assistant configuration missing 'model'")

    if "prompts" not in config:
        errors.append("Missing 'prompts' configuration")
    elif not isinstance(config["prompts"], dict):
        errors.append("'prompts' must be a dictionary")
    else:
        if "system_prompt" not in config["prompts"]:
            errors.append("Prompts configuration missing 'system_prompt'")
        if "first_message" not in config["prompts"]:
            errors.append("Prompts configuration missing 'first_message'")

    if backend_url and not backend_url.startswith(("http://", "https://")):
        errors.append(
            f"Backend URL must start with http:// or https://: {backend_url}")

    if errors:
        error_msg = "Configuration validation failed:\n" + \
            "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
