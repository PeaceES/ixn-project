#!/usr/bin/env python3
"""Quick runtime check for the local org_structure loader.
Run from workspace root with: python3 -m src.python.workshop.test_fetch_org_structure
or from this folder: python3 test_fetch_org_structure.py
"""
import json
import os
import sys

# Ensure package imports work when running the script directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agent_core import CalendarAgentCore


def main():
    agent = CalendarAgentCore(enable_tools=False)
    users = agent.fetch_org_structure()

    # Determine resolved path used by the loader for convenience
    org_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json'))
    print(f"Resolved org_structure.json path: {org_path}")
    print(f"Loaded users: {len(users)} entries")

    # Print a small sample (first 5) to verify contents
    try:
        sample = dict(list(users.items())[:5]) if isinstance(users, dict) else users[:5]
        print(json.dumps(sample, indent=2))
    except Exception as e:
        print(f"Could not serialize sample users: {e}")


if __name__ == '__main__':
    main()
