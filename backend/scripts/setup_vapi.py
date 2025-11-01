#!/usr/bin/env python3
"""
Vapi Setup Script - Creates shared assistant and tools for restaurant voice assistant.

This script loads configuration from YAML files and creates/manages Vapi resources.
"""
from pathlib import Path
import argparse
import sys
import os
from vapi.manager import VapiResourceManager


# Add backend root to path for vapi imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


def print_section(text: str):
    """Print a formatted section header."""
    print(f"\n{'-' * 60}\n{text}\n{'-' * 60}")


def list_resources(manager: VapiResourceManager):
    """List all existing tools and assistants."""
    print_section("Existing Resources")
    resources = manager.list_resources()

    assistants = resources.get("assistants", [])
    print(f"\nAssistants ({len(assistants)}):")
    for a in assistants:
        print(f"  • {a.get('name', 'Unknown')} (ID: {a.get('id', 'N/A')})")
    if not assistants:
        print("  No assistants found")

    tools = resources.get("tools", [])
    print(f"\nTools ({len(tools)}):")
    for t in tools:
        func = t.get('function', {}) if isinstance(
            t.get('function'), dict) else {}
        name = func.get('name', 'Unknown')
        print(f"  • {name} (ID: {t.get('id', 'N/A')})")
    if not tools:
        print("  No tools found")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Setup and manage Vapi assistants and tools for restaurant voice assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List existing resources
  python setup_vapi.py --list-only
  
  # Create new resources (keeps existing)
  python setup_vapi.py
  
  # Clean up and create fresh resources
  python setup_vapi.py --cleanup
  
        """
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete all existing assistants and tools before creating new ones"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list existing resources, don't create anything"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        help="Backend URL (overrides PUBLIC_BACKEND_URL env var)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Vapi API key (overrides VAPI_API_KEY env var)"
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("VAPI_API_KEY")
    backend_url = args.backend_url or os.environ.get("PUBLIC_BACKEND_URL")

    if not api_key:
        print("Error: VAPI_API_KEY required (--api-key or env var)", file=sys.stderr)
        sys.exit(1)
    if not backend_url:
        print(
            "Error: PUBLIC_BACKEND_URL required (--backend-url or env var)", file=sys.stderr)
        sys.exit(1)

    manager = VapiResourceManager(
        api_key=api_key,
        backend_url=backend_url
    )

    print_header("Vapi Setup - Restaurant Voice Assistant")
    print(f"Backend URL: {backend_url}")
    print(f"API Base URL: https://api.vapi.ai")

    try:
        list_resources(manager)
    except Exception as e:
        print(f"Warning: Could not list existing resources: {e}")
        print("Continuing anyway...")

    if args.list_only:
        print_section("Info")
        print("Listing complete. Use without --list-only to create resources.")
        return

    try:
        manager.load_and_validate_config()

        if args.cleanup:
            print_section("Cleaning Up Old Resources")
            try:
                deleted = manager.cleanup_all_resources()
                print(
                    f"\nCleaned up {deleted['assistants']} assistants and {deleted['tools']} tools")
            except Exception as e:
                print(
                    f"Warning: Cleanup failed (this is okay if API key is incorrect): {e}")
                print("Continuing with creation...")

        print_section("Creating New Resources")
        tool_map = manager.create_tools()

        if not tool_map:
            print("Error: No tools were created", file=sys.stderr)
            sys.exit(1)

        assistants = manager.client.list_assistants()
        existing_assistant = next((a for a in assistants if a.get(
            "name") == "Restaurant Voice Assistant"), None)

        if existing_assistant:
            assistant_id = existing_assistant.get("id")
            print(f"Using existing shared assistant: {assistant_id}")
        else:
            assistant_id = manager.create_assistant(tool_map)
            print(f"Created shared assistant: {assistant_id}")

        print_header("Setup Complete!")
        print(f"Assistant ID: {assistant_id}")
        print(f"\nTest at: https://dashboard.vapi.ai/assistant/{assistant_id}")
        print("\nConfig files:")
        for config_file in ["tools.yaml", "assistant.yaml", "prompts.yaml"]:
            print(f"  - vapi/config/{config_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
