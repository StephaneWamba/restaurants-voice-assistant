from typing import Dict, List, Any, Optional


def build_tool_result(tool_call_id: str, text: str) -> Dict:
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": text,
            }
        ]
    }


def build_tool_result_with_items(tool_call_id: str, text: str, items: List[Dict[str, Any]]) -> Dict:
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": text,
                "metadata": {"items": items},
            }
        ]
    }


def build_no_result(tool_call_id: str, category: Optional[str] = None, message: Optional[str] = None) -> Dict:
    """
    Build a no-result response with category-appropriate message.
    
    Args:
        tool_call_id: Tool call ID from Vapi
        category: Optional category (menu, modifiers, hours, zones)
        message: Optional custom message (uses default if not provided)
    """
    if message:
        default_message = message
    elif category == "menu":
        default_message = "I don't have information about that menu item."
    elif category == "modifiers":
        default_message = "I don't have information about those options."
    elif category == "hours":
        default_message = "I don't have operating hours information available right now."
    elif category == "zones":
        default_message = "I don't have delivery zone information available right now."
    else:
        default_message = "I don't have information about that."
    
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": default_message,
            }
        ]
    }


def extract_name_from_document(doc: Dict[str, Any]) -> Optional[str]:
    """Extract name from document metadata or content"""
    metadata = doc.get("metadata") or {}
    name = metadata.get("name") or metadata.get("title")
    if not name:
        content = doc.get("content") or ""
        parts = content.split(" - ")
        if parts:
            name = parts[0].strip()
    return name


def build_structured_items(results: List[Dict[str, Any]], category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Build structured metadata items from search results for better TTS answers.

    Args:
        results: List of search results with content and metadata
        category: Optional category (menu, modifiers, hours, zones)

    Returns:
        List of structured item dictionaries
    """
    items = []

    for doc in results[:3]:
        metadata = doc.get("metadata") or {}
        name = extract_name_from_document(doc)
        score = doc.get("score")

        if category == "menu":
            item_obj = {
                "type": "menu_item",
                "name": name,
                "price": metadata.get("price"),
                "description": metadata.get("description"),
                "score": score,
            }
        elif category == "modifiers":
            item_obj = {
                "type": "modifier",
                "name": name,
                "price_delta": metadata.get("price") or metadata.get("price_delta"),
                "required": metadata.get("required"),
                "score": score,
            }
        elif category == "hours":
            item_obj = {
                "type": "hours",
                "day_of_week": metadata.get("day_of_week"),
                "open_time": metadata.get("open_time"),
                "close_time": metadata.get("close_time"),
                "is_closed": metadata.get("is_closed"),
                "score": score,
            }
        elif category == "zones":
            item_obj = {
                "type": "zone",
                "zone_name": metadata.get("name") or metadata.get("zone_name"),
                "delivery_fee": metadata.get("fee") or metadata.get("delivery_fee"),
                "score": score,
            }
        else:
            item_obj = {
                "type": metadata.get("category") or metadata.get("type") or "unknown",
                "name": name,
                "score": score,
            }

        items.append(item_obj)

    return items
