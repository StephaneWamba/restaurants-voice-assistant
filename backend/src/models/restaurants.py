"""Pydantic models for restaurant API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional


class CreateRestaurantRequest(BaseModel):
    """Request model for creating a restaurant."""
    name: str = Field(..., description="Restaurant name",
                      example="Le Bistro Français")
    api_key: Optional[str] = Field(
        None, description="Custom API key (auto-generated if not provided)", example="api_key_abc123")
    assign_phone: bool = Field(
        True, description="Automatically assign phone number if available")
    force_twilio: bool = Field(
        False, description="Skip existing phones, force Twilio number creation")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Le Bistro Français",
                "assign_phone": True,
                "force_twilio": False
            }
        }


class RestaurantResponse(BaseModel):
    """Response model for restaurant data."""
    id: str = Field(..., description="Restaurant UUID",
                    example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    name: str = Field(..., description="Restaurant name",
                      example="Le Bistro Français")
    api_key: str = Field(..., description="Restaurant API key",
                         example="api_key_abc123")
    phone_number: Optional[str] = Field(
        None, description="Assigned phone number in E.164 format", example="+19014994418")
    created_at: str = Field(..., description="ISO 8601 timestamp",
                            example="2025-01-01T12:00:00Z")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
                "name": "Le Bistro Français",
                "api_key": "api_key_abc123",
                "phone_number": "+19014994418",
                "created_at": "2025-01-01T12:00:00Z"
            }
        }
