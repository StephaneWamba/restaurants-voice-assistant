"""
Vapi webhook endpoints for voice assistant integration.

Handles Function Tool calls from Vapi.ai, performs vector similarity search
against restaurant-specific knowledge bases, and returns structured responses
for text-to-speech synthesis.
"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from pydantic import ValidationError, BaseModel, Field
from src.models.vapi import VapiRequest
from src.services.vector_search import search_knowledge_base
from src.services.cache import clear_cache
from src.config import get_settings
from src.services.vapi_response import (
    build_tool_result_with_items,
    build_no_result,
    build_structured_items,
)
from src.middleware.request_id import get_request_id

from src.services.embedding_service import generate_embeddings_for_restaurant
from src.services.auth import verify_vapi_secret
import logging
import asyncio
import json

router = APIRouter()
logger = logging.getLogger(__name__)

TOOL_CATEGORY_MAP = {
    "get_menu_info": "menu",
    "get_modifiers_info": "modifiers",
    "get_hours_info": "hours",
    "get_zones_info": "zones",
}


class CacheInvalidateRequest(BaseModel):
    """Request model for cache invalidation."""
    restaurant_id: str = Field(..., description="Restaurant UUID",
                               example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    category: Optional[str] = Field(
        None, description="Category to invalidate (menu, modifiers, hours, zones). Omit to clear all.", example="menu")


class GenerateEmbeddingsRequest(BaseModel):
    """Request model for embedding generation."""
    restaurant_id: str = Field(..., description="Restaurant UUID",
                               example="04529052-b3dd-43c1-a534-c18d8c0f4c6d")
    category: Optional[str] = Field(
        None, description="Category to generate (menu, modifiers, hours, zones). Omit to generate all.", example="menu")


def _extract_restaurant_id(
    x_restaurant_id: Optional[str],
    vapi_request: Optional[VapiRequest] = None
) -> Optional[str]:
    """Extract restaurant_id from request headers or metadata."""
    body_restaurant_id = vapi_request.extract_restaurant_id() if vapi_request else None
    restaurant_id = x_restaurant_id or body_restaurant_id
    return restaurant_id.strip() if restaurant_id else None


def _map_tool_to_category(tool_name: Optional[str]) -> Optional[str]:
    """Map Vapi Function Tool name to internal content category."""
    if not tool_name:
        return None
    return TOOL_CATEGORY_MAP.get(tool_name)


@router.post(
    "/cache/invalidate",
    summary="Invalidate Cache",
    description="Invalidate cache entries for a restaurant/category.",
    responses={
        200: {"description": "Cache invalidated successfully"},
        401: {"description": "Invalid authentication"}
    }
)
async def invalidate_cache(
    request: CacheInvalidateRequest,
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret")
):
    """Invalidate cache entries for a restaurant/category."""
    verify_vapi_secret(x_vapi_secret)
    clear_cache(request.restaurant_id, request.category)
    return {"success": True}


@router.post(
    "/embeddings/generate",
    summary="Generate Embeddings",
    description="Generate embeddings for restaurant content.",
    responses={
        200: {"description": "Embeddings generated successfully"},
        401: {"description": "Invalid authentication"},
        500: {"description": "Failed to generate embeddings"}
    }
)
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret")
):
    """Generate embeddings for restaurant content."""
    verify_vapi_secret(x_vapi_secret)
    result = await generate_embeddings_for_restaurant(
        restaurant_id=request.restaurant_id,
        category=request.category
    )
    return result


@router.post(
    "/assistant-request",
    summary="Vapi Assistant Request",
    description="Vapi Assistant Server URL endpoint. Extracts restaurant_id from phone number and returns it in metadata for subsequent tool calls.",
    responses={
        200: {"description": "Returns restaurant_id in metadata if phone mapping found"}
    }
)
async def vapi_assistant_request(request: Request):
    """
    Vapi Assistant Server URL endpoint.

    Extracts restaurant_id from phone number and returns it in metadata.
    """
    try:
        body = await request.json()

        message_obj = body.get("message", {})
        phone_number = None
        if isinstance(message_obj, dict):
            phone_value = message_obj.get(
                "phoneNumber") or message_obj.get("phone_number")
            if isinstance(phone_value, str):
                phone_number = phone_value
            elif isinstance(phone_value, dict):
                phone_number = phone_value.get(
                    "number") or phone_value.get("phoneNumber")

            if not phone_number:
                call_obj = message_obj.get("call", {})
                if isinstance(call_obj, dict):
                    phone_value = call_obj.get(
                        "phoneNumber") or call_obj.get("phone_number")
                    if isinstance(phone_value, str):
                        phone_number = phone_value
                    elif isinstance(phone_value, dict):
                        phone_number = phone_value.get(
                            "number") or phone_value.get("phoneNumber")

        if phone_number and isinstance(phone_number, str):
            from src.services.phone_mapping import get_restaurant_id_from_phone
            restaurant_id = get_restaurant_id_from_phone(phone_number)
            if restaurant_id:
                return {
                    "metadata": {
                        "restaurant_id": restaurant_id,
                        "phoneNumber": phone_number
                    }
                }
    except Exception as e:
        request_id = get_request_id(request)
        logger.error(
            f"Assistant request error: {e}",
            exc_info=True,
            extra={"request_id": request_id}
        )

    return {}


@router.post(
    "/knowledge-base",
    summary="Vapi Knowledge Base",
    description="Main Vapi webhook endpoint for Function Tool calls. Performs vector similarity search and returns restaurant-specific results.",
    responses={
        200: {"description": "Tool result with search results"},
        401: {"description": "Invalid authentication"},
        422: {"description": "Missing restaurant_id or invalid request format"},
        500: {"description": "Internal server error"}
    }
)
async def vapi_knowledge_base(
    request: Request,
    x_restaurant_id: Optional[str] = Header(
        None, alias="X-Restaurant-Id", description="Restaurant UUID (can also be in metadata)"),
    x_vapi_secret: Optional[str] = Header(
        None, alias="X-Vapi-Secret", description="Vapi webhook secret")
):
    """Main Vapi webhook endpoint for Function Tool calls."""
    settings = get_settings()

    try:
        if not x_vapi_secret or x_vapi_secret != settings.vapi_secret_key:
            raise HTTPException(
                status_code=401, detail="Invalid authentication")

        body_bytes = await request.body()

        try:
            vapi_request = VapiRequest.parse_raw(body_bytes)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid request format: {str(e)}"
            )

        query_text = vapi_request.extract_query()
        tool_call_id = vapi_request.extract_tool_call_id()
        tool_name = vapi_request.extract_tool_name()

        if not query_text:
            raise HTTPException(
                status_code=422, detail="Missing query parameter")

        if not tool_call_id:
            raise HTTPException(status_code=422, detail="Missing toolCallId")

        restaurant_id = (x_restaurant_id or
                         dict(request.query_params).get("restaurant_id") or
                         _extract_restaurant_id(None, vapi_request))

        if not restaurant_id:
            try:
                from src.services.phone_mapping import get_restaurant_id_from_phone

                body_dict = json.loads(body_bytes.decode('utf-8'))
                message_obj = body_dict.get("message", {})
                phone_number = None

                if isinstance(message_obj, dict):
                    phone_value = message_obj.get(
                        "phoneNumber") or message_obj.get("phone_number")
                    if isinstance(phone_value, str):
                        phone_number = phone_value
                    elif isinstance(phone_value, dict):
                        phone_number = phone_value.get(
                            "number") or phone_value.get("phoneNumber")

                    if not phone_number:
                        call_obj = message_obj.get("call", {})
                        if isinstance(call_obj, dict):
                            phone_value = call_obj.get(
                                "phoneNumber") or call_obj.get("phone_number")
                            if isinstance(phone_value, str):
                                phone_number = phone_value
                            elif isinstance(phone_value, dict):
                                phone_number = phone_value.get(
                                    "number") or phone_value.get("phoneNumber")

                if phone_number and isinstance(phone_number, str):
                    restaurant_id = get_restaurant_id_from_phone(phone_number)
            except Exception as e:
                request_id = get_request_id(request)
                logger.error(
                    f"Error extracting restaurant_id: {e}",
                    exc_info=True,
                    extra={"request_id": request_id}
                )

        if not restaurant_id:
            raise HTTPException(
                status_code=422,
                detail="restaurant_id is required. Provide via X-Restaurant-Id header, query param, metadata.restaurant_id, or ensure phone number is in call metadata."
            )

        category = _map_tool_to_category(tool_name)

        try:
            results = await asyncio.wait_for(
                search_knowledge_base(
                    query=query_text,
                    restaurant_id=restaurant_id,
                    category=category,
                    limit=5
                ),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            return build_no_result(
                tool_call_id,
                "I'm experiencing a delay retrieving that information. Please try again in a moment."
            )

        if not results:
            return build_no_result(tool_call_id, category=category)

        response_text = "\n\n".join([doc["content"] for doc in results[:3]])
        items = build_structured_items(results, category)

        return build_tool_result_with_items(tool_call_id, response_text, items)

    except ValidationError as e:
        request_id = get_request_id(request)
        logger.error(
            f"Validation error: {e.errors()}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=422, detail=f"Invalid request format: {e.errors()}")
    except HTTPException:
        raise
    except Exception as e:
        request_id = get_request_id(request)
        logger.error(
            f"Error processing knowledge-base request: {e}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise HTTPException(status_code=500, detail=str(e))
