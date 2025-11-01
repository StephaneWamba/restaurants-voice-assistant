"""
Vector similarity search service for knowledge base queries.

Performs semantic search using pgvector against restaurant-specific
document embeddings with automatic caching and tenant isolation.
"""
from typing import Optional, List, Dict, Any
from src.services.supabase_client import get_supabase_client
from src.services.embedding_service import generate_embedding
from src.services.cache import get_cached_result, set_cached_result
import logging

logger = logging.getLogger(__name__)


async def search_knowledge_base(
    query: str,
    restaurant_id: str,
    category: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search knowledge base using vector similarity search.

    Uses OpenAI embeddings and pgvector for semantic search with automatic
    caching (60s TTL) and multi-tenant isolation.

    Args:
        query: Search query text
        restaurant_id: Restaurant UUID for tenant isolation
        category: Optional category filter (menu, modifiers, hours, zones)
        limit: Maximum number of results (default: 5)

    Returns:
        List of documents with keys: content, metadata, score
    """
    cached = get_cached_result(restaurant_id, query, category)
    if cached is not None:
        return cached

    query_embedding = await generate_embedding(query)

    rpc_params = {
        "query_embedding": query_embedding,
        "query_restaurant_id": restaurant_id,
        "match_count": limit
    }

    if category:
        rpc_params["query_category"] = category

    supabase = get_supabase_client()
    response = supabase.rpc("search_documents", rpc_params).execute()

    results = [
        {
            "content": doc["content"],
            "metadata": doc["metadata"],
            "score": doc["similarity"]
        }
        for doc in response.data
    ]

    set_cached_result(restaurant_id, query, results, category)

    return results
