#!/usr/bin/env python3
"""
Database seeding script for restaurant voice assistant.

Creates a restaurant and seeds it with sample data:
- Menu items
- Modifiers
- Operating hours
- Delivery zones

Optionally generates embeddings for all data.
"""

from src.services.supabase_client import get_supabase_service_client
import os
import sys
import argparse
from pathlib import Path
from uuid import uuid4
import requests

# Add backend root to path BEFORE importing src modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_restaurant(name: str, api_key: str = None) -> str:
    """Create a restaurant and return its ID."""
    supabase = get_supabase_service_client()

    if api_key is None:
        api_key = f"api_key_{uuid4().hex[:16]}"

    result = supabase.table("restaurants").insert({
        "name": name,
        "api_key": api_key
    }).execute()

    restaurant_id = result.data[0]["id"]
    print(f"Created restaurant: {name} (ID: {restaurant_id})")
    return restaurant_id


def seed_menu_items(restaurant_id: str):
    """Seed menu items for a restaurant."""
    supabase = get_supabase_service_client()

    menu_items = [
        {
            "restaurant_id": restaurant_id,
            "name": "Coq au Vin",
            "description": "Classic French dish with chicken braised in wine, mushrooms, and bacon",
            "price": 24.99,
            "category": "Main Course"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Bouillabaisse",
            "description": "Traditional Provençal fish stew with saffron, fennel, and herbs",
            "price": 32.50,
            "category": "Main Course"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Duck Confit",
            "description": "Slow-cooked duck leg with crispy skin, served with potatoes",
            "price": 28.75,
            "category": "Main Course"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Ratatouille",
            "description": "Vegetable stew with eggplant, zucchini, bell peppers, and tomatoes",
            "price": 18.50,
            "category": "Vegetarian"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Crème Brûlée",
            "description": "Vanilla custard with caramelized sugar topping",
            "price": 8.99,
            "category": "Dessert"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Tarte Tatin",
            "description": "Upside-down caramelized apple tart",
            "price": 9.50,
            "category": "Dessert"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "French Onion Soup",
            "description": "Rich beef broth with caramelized onions, topped with cheese and bread",
            "price": 12.99,
            "category": "Starter"
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Escargots",
            "description": "Snails cooked in garlic butter and parsley",
            "price": 14.50,
            "category": "Starter"
        }
    ]

    result = supabase.table("menu_items").insert(menu_items).execute()
    print(f"Seeded {len(result.data)} menu items")
    return len(result.data)


def seed_modifiers(restaurant_id: str):
    """Seed modifiers for a restaurant."""
    supabase = get_supabase_service_client()

    modifiers = [
        {
            "restaurant_id": restaurant_id,
            "name": "Extra Cheese",
            "description": "Additional cheese topping",
            "price": 2.50
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Extra Sauce",
            "description": "Additional sauce on the side",
            "price": 1.50
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Gluten-Free Option",
            "description": "Gluten-free alternative",
            "price": 3.00
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Vegetarian Substitute",
            "description": "Vegetarian protein alternative",
            "price": 4.00
        },
        {
            "restaurant_id": restaurant_id,
            "name": "Spicy Level",
            "description": "Add extra spice",
            "price": 0.00
        }
    ]

    result = supabase.table("modifiers").insert(modifiers).execute()
    print(f"Seeded {len(result.data)} modifiers")
    return len(result.data)


def seed_operating_hours(restaurant_id: str):
    """Seed operating hours for a restaurant."""
    supabase = get_supabase_service_client()

    hours = [
        {"restaurant_id": restaurant_id, "day_of_week": "Mon",
            "open_time": "11:00", "close_time": "22:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Tue",
            "open_time": "11:00", "close_time": "22:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Wed",
            "open_time": "11:00", "close_time": "22:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Thu",
            "open_time": "11:00", "close_time": "22:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Fri",
            "open_time": "11:00", "close_time": "23:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Sat",
            "open_time": "12:00", "close_time": "23:00", "is_closed": False},
        {"restaurant_id": restaurant_id, "day_of_week": "Sun",
            "open_time": "12:00", "close_time": "21:00", "is_closed": False}
    ]

    result = supabase.table("operating_hours").insert(hours).execute()
    print(f"Seeded {len(result.data)} operating hours")
    return len(result.data)


def seed_delivery_zones(restaurant_id: str):
    """Seed delivery zones for a restaurant."""
    supabase = get_supabase_service_client()

    zones = [
        {
            "restaurant_id": restaurant_id,
            "zone_name": "Downtown",
            "description": "Within 3km radius, free delivery for orders over $25",
            "delivery_fee": 4.50,
            "min_order": 25.00
        },
        {
            "restaurant_id": restaurant_id,
            "zone_name": "Uptown",
            "description": "3-6km radius",
            "delivery_fee": 6.00,
            "min_order": 30.00
        },
        {
            "restaurant_id": restaurant_id,
            "zone_name": "Suburbs",
            "description": "6-10km radius",
            "delivery_fee": 8.50,
            "min_order": 40.00
        }
    ]

    result = supabase.table("delivery_zones").insert(zones).execute()
    print(f"Seeded {len(result.data)} delivery zones")
    return len(result.data)


def generate_embeddings(restaurant_id: str, backend_url: str = "http://localhost:8000"):
    """Generate embeddings for all restaurant data."""
    print(f"\nGenerating embeddings via {backend_url}...")

    # Get VAPI_SECRET_KEY from environment (same as backend uses)
    secret = os.environ.get("VAPI_SECRET_KEY")
    if not secret:
        print("Warning: VAPI_SECRET_KEY not found. Using empty secret.")
        secret = ""

    headers = {
        "X-Vapi-Secret": secret,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{backend_url}/api/embeddings/generate",
            json={"restaurant_id": restaurant_id},
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        print(
            f"Generated {result.get('embeddings_generated', 0)} embeddings")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error generating embeddings: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Seed database with restaurant data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create restaurant and seed all data
  python seed_database.py --restaurant-name "Le Bistro Français"
  
  # Seed with specific restaurant ID
  python seed_database.py --restaurant-id <uuid>
  
  # Seed and generate embeddings
  python seed_database.py --restaurant-name "Le Bistro" --generate-embeddings
  
        """
    )

    parser.add_argument(
        "--restaurant-name",
        type=str,
        help="Name of the restaurant to create"
    )
    parser.add_argument(
        "--restaurant-id",
        type=str,
        help="Existing restaurant ID (skip creation)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for new restaurant (auto-generated if not provided)"
    )
    parser.add_argument(
        "--generate-embeddings",
        action="store_true",
        help="Generate embeddings after seeding"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="http://localhost:8000",
        help="Backend URL for embedding generation (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--skip-menu",
        action="store_true",
        help="Skip menu items seeding"
    )
    parser.add_argument(
        "--skip-modifiers",
        action="store_true",
        help="Skip modifiers seeding"
    )
    parser.add_argument(
        "--skip-hours",
        action="store_true",
        help="Skip operating hours seeding"
    )
    parser.add_argument(
        "--skip-zones",
        action="store_true",
        help="Skip delivery zones seeding"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.restaurant_id and not args.restaurant_name:
        print("Error: Either --restaurant-id or --restaurant-name is required", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Database Seeding - Restaurant Voice Assistant")
    print("=" * 60)

    # Create or use existing restaurant
    if args.restaurant_id:
        restaurant_id = args.restaurant_id
        print(f"\nUsing existing restaurant ID: {restaurant_id}")
    else:
        restaurant_id = create_restaurant(args.restaurant_name, args.api_key)

    print(f"\nRestaurant ID: {restaurant_id}")
    print("-" * 60)

    # Seed data
    if not args.skip_menu:
        seed_menu_items(restaurant_id)

    if not args.skip_modifiers:
        seed_modifiers(restaurant_id)

    if not args.skip_hours:
        seed_operating_hours(restaurant_id)

    if not args.skip_zones:
        seed_delivery_zones(restaurant_id)

    # Generate embeddings if requested
    if args.generate_embeddings:
        print("\n" + "-" * 60)
        generate_embeddings(restaurant_id, args.backend_url)

    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"\nRestaurant ID: {restaurant_id}")
    if args.generate_embeddings:
        print("\nNext step: Run setup_vapi.py to create Vapi assistant")
        print(
            f"  python scripts/setup_vapi.py --restaurant-id {restaurant_id} --backend-url <your-ngrok-url>")


if __name__ == "__main__":
    main()
