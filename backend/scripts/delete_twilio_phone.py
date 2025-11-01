#!/usr/bin/env python3
"""Delete existing Twilio phone number from Vapi."""
from src.services.supabase_client import get_supabase_service_client
from vapi.client import VapiClient
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


api_key = os.environ.get("VAPI_API_KEY")
if not api_key:
    print("Error: VAPI_API_KEY required")
    sys.exit(1)

client = VapiClient(api_key=api_key)
supabase = get_supabase_service_client()

print("=" * 60)
print("Delete Twilio Phone Number")
print("=" * 60)

vapi_phones = client.list_phone_numbers()
twilio_phones = [p for p in vapi_phones if p.get("provider") == "twilio"]

if not twilio_phones:
    print("\nNo Twilio phone numbers found in Vapi.")
    sys.exit(0)

print(f"\nFound {len(twilio_phones)} Twilio phone number(s):")
for p in twilio_phones:
    number = p.get("number")
    phone_id = p.get("id")
    print(f"  {number} (ID: {phone_id})")

print("\nDeleting Twilio phone numbers...")
for p in twilio_phones:
    number = p.get("number")
    phone_id = p.get("id")

    try:
        mapping = supabase.table("restaurant_phone_mappings").select("restaurant_id").eq(
            "phone_number", number.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")).execute()

        if mapping.data:
            restaurant_id = mapping.data[0].get("restaurant_id")
            print(f"\n  Removing mapping for {number} -> {restaurant_id}...")
            supabase.table("restaurant_phone_mappings").delete().eq("phone_number", number.replace(
                " ", "").replace("(", "").replace(")", "").replace("-", "")).execute()

        print(f"  Deleting {number} from Vapi...")
        client.delete_phone_number(phone_id)
        print(f"  Deleted {number}")
    except Exception as e:
        print(f"  Error deleting {number}: {e}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
