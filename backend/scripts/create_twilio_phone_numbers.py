#!/usr/bin/env python3
"""
Batch script to create and assign Twilio phone numbers to multiple restaurants.

For single restaurant creation, use POST /api/restaurants (automatically creates phones).
This script is for bulk operations on existing restaurants without phones.
"""
from vapi.client import VapiClient
from src.services.twilio_service import create_and_assign_twilio_phone
from src.services.supabase_client import get_supabase_service_client
from vapi.manager import VapiResourceManager
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


api_key = os.environ.get("VAPI_API_KEY")
backend_url = os.environ.get("PUBLIC_BACKEND_URL")
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if not api_key:
    print("Error: VAPI_API_KEY not set", file=sys.stderr)
    sys.exit(1)

if not backend_url:
    print("Error: PUBLIC_BACKEND_URL not set", file=sys.stderr)
    sys.exit(1)

if not twilio_account_sid:
    print("Error: TWILIO_ACCOUNT_SID not set", file=sys.stderr)
    sys.exit(1)

if not twilio_auth_token:
    print("Error: TWILIO_AUTH_TOKEN not set", file=sys.stderr)
    print("\nTo use Twilio for automatic phone number creation:")
    print("1. Sign up for Twilio: https://www.twilio.com/")
    print("2. Get your Account SID and Auth Token from Console")
    print("3. Set environment variables:")
    print("   - TWILIO_ACCOUNT_SID=your_account_sid")
    print("   - TWILIO_AUTH_TOKEN=your_auth_token")
    sys.exit(1)

client = VapiClient(api_key=api_key)
supabase = get_supabase_service_client()
manager = VapiResourceManager(api_key=api_key, backend_url=backend_url)

print("=" * 60)
print("Automatic Phone Number Creation via Twilio")
print("=" * 60)

# Get shared assistant
assistants = manager.client.list_assistants()
assistant = next((a for a in assistants if a.get("name")
                 == "Restaurant Voice Assistant"), None)

if not assistant:
    print("\nX No shared assistant found!")
    sys.exit(1)

assistant_id = assistant.get("id")
print(f"\nFound shared assistant: {assistant_id}")

# Get restaurants without phone mappings
all_restaurants = supabase.table("restaurants").select("id,name").execute()
existing_mappings = supabase.table(
    "restaurant_phone_mappings").select("restaurant_id").execute()
mapped_restaurant_ids = {m.get("restaurant_id")
                         for m in existing_mappings.data}
unmapped_restaurants = [r for r in all_restaurants.data if r.get(
    "id") not in mapped_restaurant_ids]

print(f"\nStatus:")
print(f"  Total restaurants: {len(all_restaurants.data)}")
print(f"  With phone mappings: {len(mapped_restaurant_ids)}")
print(f"  Need phone numbers: {len(unmapped_restaurants)}")

if not unmapped_restaurants:
    print("\nAll restaurants have phone numbers!")
    sys.exit(0)

print(f"\nCreating phone numbers via Twilio API (batch mode)...")
print(f"  Twilio Account SID: {twilio_account_sid[:10]}...")

restaurants_to_process = unmapped_restaurants[:10]
created_count = 0

print(f"\nProcessing {len(restaurants_to_process)} restaurant(s)...")
for restaurant in restaurants_to_process:
    restaurant_id = restaurant.get("id")
    restaurant_name = restaurant.get("name")

    print(f"\n  [{restaurant_name}] Creating phone number...", end=" ")

    try:
        phone_number = create_and_assign_twilio_phone(
            restaurant_id=restaurant_id,
            assistant_id=assistant_id,
            client=client,
            manager=manager,
            twilio_account_sid=twilio_account_sid,
            twilio_auth_token=twilio_auth_token
        )

        if phone_number:
            print(f"OK -> {phone_number}")
            created_count += 1
        else:
            print("FAILED")
    except Exception as e:
        print(f"ERROR: {e}")

if created_count > 0:
    print(
        f"\nSuccessfully created {created_count} phone number(s) via Twilio!")
else:
    print(f"\nCould not create phone numbers")
    print(f"\nTroubleshooting:")
    print(f"  1. Verify TWILIO_ACCOUNT_SID is correct")
    print(f"  2. Set TWILIO_AUTH_TOKEN if required by Vapi")
    print(f"  3. Ensure Twilio account has available phone numbers/quota")
    print(f"  4. Check Twilio account billing is set up")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
