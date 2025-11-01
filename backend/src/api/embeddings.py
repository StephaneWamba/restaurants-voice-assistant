"""
Embedding management endpoints.

Endpoints for generating embeddings and managing cache.
All endpoints require authentication via X-Vapi-Secret header.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, Field
from src.services.embedding_service import generate_embeddings_for_restaurant
from src.config import get_settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def _verify_secret(x_vapi_secret: Optional[str]) -> None:
    """Verify Vapi secret for endpoint authentication."""
    if not x_vapi_secret or x_vapi_secret != settings.vapi_secret_key:
        logger.warning("Invalid or missing secret on embeddings endpoint")
        raise HTTPException(status_code=401, detail="Invalid authentication")


class GenerateEmbeddingsRequest(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant UUID",
                               example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    category: str | None = Field(
        None, description="Category to generate (menu, modifiers, hours, zones)", example="menu")


class CacheInvalidateRequest(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant UUID",
                               example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    category: str | None = Field(
        None, description="Category to invalidate (menu, modifiers, hours, zones)", example="menu")


@router.post(
    "/generate",
    summary="Generate Embeddings",
    description="Generate embeddings for restaurant data. Requires X-Vapi-Secret header for authentication.",
    responses={
        200: {
            "description": "Embeddings generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
                        "embeddings_generated": 23
                    }
                }
            }
        },
        401: {"description": "Invalid authentication"},
        500: {"description": "Failed to generate embeddings"}
    }
)
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret")
):
    _verify_secret(x_vapi_secret)

    try:
        result = await generate_embeddings_for_restaurant(
            restaurant_id=request.restaurant_id,
            category=request.category
        )
        return result
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embeddings"
        )


@router.post(
    "/cache/invalidate",
    summary="Invalidate Cache",
    description="Force invalidate cache for a restaurant. Requires X-Vapi-Secret header for authentication.",
    responses={
        200: {
            "description": "Cache invalidated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Cache cleared for restaurant 04529052-b3dd-43c1-a534-c18d8c0f4c6d"
                    }
                }
            }
        },
        401: {"description": "Invalid authentication"},
        500: {"description": "Failed to invalidate cache"}
    }
)
async def invalidate_cache(
    request: CacheInvalidateRequest,
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret")
):
    _verify_secret(x_vapi_secret)

    from src.services.cache import clear_cache

    try:
        clear_cache(request.restaurant_id, request.category)
        return {
            "status": "success",
            "message": f"Cache cleared for restaurant {request.restaurant_id}"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )
