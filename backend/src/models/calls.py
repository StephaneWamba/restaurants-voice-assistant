"""
Pydantic models for call history API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateCallRequest(BaseModel):
    """Request model for creating a call history record."""
    restaurant_id: Optional[str] = Field(None, description="Restaurant UUID (also accepted via X-Restaurant-Id header)", example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    started_at: datetime = Field(..., description="Call start time (ISO 8601)", example="2025-01-01T12:00:00Z")
    ended_at: Optional[datetime] = Field(None, description="Call end time (ISO 8601)", example="2025-01-01T12:05:00Z")
    duration_seconds: Optional[int] = Field(None, description="Call duration in seconds", example=300)
    caller: Optional[str] = Field(None, description="Caller phone number (E.164 format)", example="+1234567890")
    outcome: Optional[str] = Field(None, description="Call outcome", example="completed")
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="Call messages/transcript", example=[
        {"role": "user", "content": "What's on your menu?", "timestamp": "2025-01-01T12:00:30Z"}
    ])

    class Config:
        json_schema_extra = {
            "example": {
                "started_at": "2025-01-01T12:00:00Z",
                "ended_at": "2025-01-01T12:05:00Z",
                "duration_seconds": 300,
                "caller": "+1234567890",
                "outcome": "completed",
                "messages": [
                    {"role": "user", "content": "What's on your menu?", "timestamp": "2025-01-01T12:00:30Z"},
                    {"role": "assistant", "content": "We have croissants...", "timestamp": "2025-01-01T12:00:35Z"}
                ]
            }
        }

