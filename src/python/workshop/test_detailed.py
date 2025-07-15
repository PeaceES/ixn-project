#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services.calendar_mcp_server import startup_event, rooms_data, calendars_data, events_data

async def test():
    # Test the startup
    await startup_event()
    
    # Check if data was loaded
    with open('test_results.txt', 'w') as f:
        f.write("=== MCP Server Test Results ===\n")
        f.write(f"Rooms loaded: {len(rooms_data.get('rooms', []))}\n")
        f.write(f"Calendars created: {len(calendars_data.get('calendars', []))}\n")
        f.write(f"Events loaded: {len(events_data.get('events', []))}\n")
        f.write("\n=== Rooms Data ===\n")
        f.write(json.dumps(rooms_data, indent=2))
        f.write("\n=== Calendars Data ===\n")
        f.write(json.dumps(calendars_data, indent=2))
        f.write("\n=== Events Data (first 3) ===\n")
        events_sample = events_data.get('events', [])[:3]
        f.write(json.dumps(events_sample, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
