#!/usr/bin/env python3
"""
Complete reset and test script.

1. Resets database (drops all tables, re-runs migrations)
2. Resets Vapi (deletes assistant and tools)
3. Tests complete workflow:
   - Create restaurant (auto-creates phone)
   - Seed data
   - Generate embeddings
   - Test voice call flow
"""
import asyncio
from src.services.embedding_service import generate_embeddings_for_restaurant
from vapi.manager import VapiResourceManager
from src.services.supabase_client import get_supabase_service_client
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


api_key = os.environ.get("VAPI_API_KEY")
backend_url = os.environ.get("PUBLIC_BACKEND_URL")
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if not api_key or not backend_url:
    print("Error: VAPI_API_KEY and PUBLIC_BACKEND_URL required", file=sys.stderr)
    sys.exit(1)

supabase = get_supabase_service_client()
manager = VapiResourceManager(api_key=api_key, backend_url=backend_url)

print("=" * 60)
print("COMPLETE RESET AND TEST")
print("=" * 60)

# Step 1: Reset Database
print("\n[Step 1] Resetting database...")
print("  Manual step required: Please run in Supabase SQL Editor:")
print("     1. Open Supabase Dashboard → SQL Editor")
print("     2. Run: supabase/migrations/999_drop_all_tables.sql")
print("     3. Run: supabase/migrations/000_clean_schema.sql")
print("     4. Run: supabase/migrations/015_fix_service_role_policies.sql")
print("     5. Run: supabase/migrations/016_add_phone_mapping_table.sql")
print("  Then press Enter to continue...")
input()

# Step 2: Reset Vapi
print("\n[Step 2] Resetting Vapi resources...")
try:
    deleted = manager.cleanup_all_resources()
    print(f"  Deleted {deleted['assistants']} assistant(s)")
    print(f"  Deleted {deleted['tools']} tool(s)")
except Exception as e:
    print(f"  Warning: Could not cleanup Vapi: {e}")

# Step 3: Recreate Vapi setup
print("\n[Step 3] Recreating Vapi assistant and tools...")
try:
    manager.load_and_validate_config()
    tool_map = manager.create_tools()
    assistant_id = manager.create_assistant(tool_map)
    print(f"  Created assistant: {assistant_id}")
    print(f"  Created {len(tool_map)} tool(s)")
except Exception as e:
    print(f"  Error: {e}")
    sys.exit(1)

# Step 4: Test restaurant creation with auto phone
print("\n[Step 4] Testing restaurant creation (auto phone)...")
restaurant_name = "Test Restaurant"

try:
    from uuid import uuid4
    from src.services.phone_service import assign_phone_to_restaurant

    api_key_str = f"api_key_{uuid4().hex[:16]}"
    result = supabase.table("restaurants").insert({
        "name": restaurant_name,
        "api_key": api_key_str
    }).execute()

    if not result.data:
        raise Exception("Failed to create restaurant")

    restaurant_id = result.data[0]["id"]
    print(f"  Created restaurant: {restaurant_name} (ID: {restaurant_id})")

    phone_number = assign_phone_to_restaurant(restaurant_id, force_twilio=True)
    if phone_number:
        print(f"  Auto-assigned Twilio phone: {phone_number}")
    else:
        print(f"  No phone assigned (check Twilio credentials or available numbers)")

except Exception as e:
    print(f"  Error creating restaurant: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Seed data
print("\n[Step 5] Seeding restaurant data...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from seed_database import seed_menu_items, seed_modifiers, seed_operating_hours, seed_delivery_zones

    seed_menu_items(restaurant_id)
    print("  Seeded menu items")

    seed_modifiers(restaurant_id)
    print("  Seeded modifiers")

    seed_operating_hours(restaurant_id)
    print("  Seeded hours")

    seed_delivery_zones(restaurant_id)
    print("  Seeded zones")
except Exception as e:
    print(f"  Error seeding data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Generate embeddings
print("\n[Step 6] Generating embeddings...")
try:
    result = asyncio.run(generate_embeddings_for_restaurant(restaurant_id))
    total = result.get("embeddings_generated", 0)
    print(f"  Generated {total} embedding(s)")
except Exception as e:
    print(f"  Error generating embeddings: {e}")
    sys.exit(1)

# Step 7: Verify setup
print("\n[Step 7] Verifying setup...")
try:
    restaurants = supabase.table("restaurants").select("id,name").execute()
    print(f"  Restaurants in DB: {len(restaurants.data)}")

    phone_mappings = supabase.table(
        "restaurant_phone_mappings").select("*").execute()
    print(f"  Phone mappings: {len(phone_mappings.data)}")

    embeddings = supabase.table("document_embeddings").select(
        "id").eq("restaurant_id", restaurant_id).execute()
    print(f"  Embeddings for restaurant: {len(embeddings.data)}")

except Exception as e:
    print(f"  Error verifying: {e}")

print("\n" + "=" * 60)
print("RESET AND SETUP COMPLETE!")
print("=" * 60)
print(f"\nRestaurant ID: {restaurant_id}")
print(f"Assistant ID: {assistant_id}")
if phone_number:
    print(f"Phone Number: {phone_number}")
print("\nNext steps:")
print("1. Test a call via Vapi Dashboard")
print("2. Ask: 'What's on your menu?'")
print("3. Check backend logs for tool calls")
