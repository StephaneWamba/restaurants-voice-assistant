from cachetools import TTLCache
from typing import Optional
from src.config import get_settings

settings = get_settings()

_cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl_seconds)


def get_cache_key(restaurant_id: str, query: str, category: Optional[str] = None) -> str:
    """Generate cache key for a query"""
    category_str = category or "all"
    return f"{restaurant_id}:{category_str}:{query}"


def get_cached_result(restaurant_id: str, query: str, category: Optional[str] = None):
    """Retrieve cached search result"""
    key = get_cache_key(restaurant_id, query, category)
    return _cache.get(key)


def set_cached_result(restaurant_id: str, query: str, results: list, category: Optional[str] = None):
    """Store search result in cache"""
    key = get_cache_key(restaurant_id, query, category)
    _cache[key] = results


def clear_cache(restaurant_id: str, category: Optional[str] = None):
    """Clear cache for a specific restaurant/category"""
    keys_to_delete = []

    for key in list(_cache.keys()):
        if key.startswith(f"{restaurant_id}:"):
            if category is None or f":{category}:" in key:
                keys_to_delete.append(key)

    for key in keys_to_delete:
        del _cache[key]
