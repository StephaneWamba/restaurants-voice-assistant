"""
Authentication utilities for API endpoints.
"""
from fastapi import HTTPException
from typing import Optional
from src.config import get_settings


def verify_vapi_secret(x_vapi_secret: Optional[str]) -> None:
    """Verify Vapi secret header matches configured secret."""
    settings = get_settings()
    if not x_vapi_secret or x_vapi_secret != settings.vapi_secret_key:
        raise HTTPException(status_code=401, detail="Invalid authentication")
