from openai import AsyncOpenAI
from src.config import get_settings
from src.services.supabase_client import get_supabase_client, get_supabase_service_client
from typing import Optional

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a text using OpenAI"""
    response = await openai_client.embeddings.create(
        model=settings.embedding_model,
        input=text
    )
    return response.data[0].embedding


async def generate_embeddings_for_restaurant(
    restaurant_id: str,
    category: Optional[str] = None
) -> dict:
    """
    Generate embeddings for all documents of a restaurant

    Args:
        restaurant_id: UUID of the restaurant
        category: Optional category filter (menu, modifiers, hours, zones)

    Returns:
        dict with count of generated embeddings
    """
    supabase_read = get_supabase_client()
    supabase_write = get_supabase_service_client()

    categories_to_process = [category] if category else [
        "menu", "modifiers", "hours", "zones"]
    total_generated = 0

    for cat in categories_to_process:
        if cat == "menu":
            data = supabase_read.table("menu_items").select(
                "*").eq("restaurant_id", restaurant_id).execute()
            documents = [
                {
                    "content": f"{item['name']} - {item['description']} - ${item['price']}",
                    "metadata": item,
                    "category": "menu"
                }
                for item in data.data
            ]
        elif cat == "modifiers":
            data = supabase_read.table("modifiers").select(
                "*").eq("restaurant_id", restaurant_id).execute()
            documents = [
                {
                    "content": f"{mod['name']} - {mod.get('description', '')} - ${mod.get('price', 0)}",
                    "metadata": mod,
                    "category": "modifiers"
                }
                for mod in data.data
            ]
        elif cat == "hours":
            data = supabase_read.table("operating_hours").select(
                "*").eq("restaurant_id", restaurant_id).execute()
            documents = [
                {
                    "content": f"{h['day_of_week']}: {h['open_time']} - {h['close_time']}",
                    "metadata": h,
                    "category": "hours"
                }
                for h in data.data
            ]
        elif cat == "zones":
            data = supabase_read.table("delivery_zones").select(
                "*").eq("restaurant_id", restaurant_id).execute()
            documents = [
                {
                    "content": f"Delivery zone {z.get('zone_name')}: €{z.get('delivery_fee') if z.get('delivery_fee') is not None else 0}",
                    "metadata": z,
                    "category": "zones"
                }
                for z in data.data
            ]
        else:
            continue

        for doc in documents:
            embedding = await generate_embedding(doc["content"])

            supabase_write.table("document_embeddings").upsert({
                "restaurant_id": restaurant_id,
                "content": doc["content"],
                "embedding": embedding,
                "category": doc["category"],
                "metadata": doc["metadata"]
            }).execute()

            total_generated += 1

    return {
        "status": "success",
        "restaurant_id": restaurant_id,
        "embeddings_generated": total_generated
    }
