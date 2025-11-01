"""
Vapi setup and management module.

Provides utilities for configuring and managing Vapi assistants, tools, and resources.
"""

from .client import VapiClient
from .config_loader import load_config, validate_config
from .manager import VapiResourceManager

__all__ = ["VapiClient", "load_config", "validate_config", "VapiResourceManager"]

