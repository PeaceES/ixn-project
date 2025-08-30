#!/usr/bin/env python3
"""Test script for entity extraction and email lookup."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.calendar_mcp_server import extract_entity_from_description, find_entity_email

# Test cases
test_descriptions = [
    "Event for 50 people organized by the AI Society.",
    "Event for 30 people organized by AI Society",
    "Event for 20 people, organized by Allison Hill for the Engineering Department.",
    "Monthly meeting organized by Computing Department.",
    "Workshop organized by Drama Society for students",
    "Regular meeting",  # No entity
    ""  # Empty description
]

print("Testing entity extraction and email lookup:\n")

for desc in test_descriptions:
    print(f"Description: {desc}")
    entity = extract_entity_from_description(desc)
    if entity:
        print(f"  Extracted entity: {entity}")
        email = find_entity_email(entity)
        if email:
            print(f"  Entity email: {email}")
        else:
            print(f"  Entity email: Not found")
    else:
        print(f"  No entity found")
    print()
