#!/usr/bin/env python3

import sys
import os
import json
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to get access to global variables
import services.calendar_mcp_server as mcp_server

@pytest.mark.asyncio
async def test():
    # Call startup_event which should load everything
    await mcp_server.startup_event()
    
    # Now check the global variables
    rooms_count = len(mcp_server.rooms_data.get('rooms', []))
    calendars_count = len(mcp_server.calendars_data.get('calendars', []))
    events_count = len(mcp_server.events_data.get('events', []))
    users_count = len(mcp_server.user_directory)
    
    with open('test_startup.txt', 'w') as f:
        f.write("=== Startup Test Results ===\\n")
        f.write(f"Rooms loaded: {rooms_count}\\n")
        f.write(f"Calendars created: {calendars_count}\\n")
        f.write(f"Events loaded: {events_count}\\n")
        f.write(f"Users loaded: {users_count}\\n")
        
        if rooms_count > 0:
            f.write(f"\\n=== First Room Data ===\\n")
            first_room = mcp_server.rooms_data['rooms'][0]
            f.write(json.dumps(first_room, indent=2))
            
        if calendars_count > 0:
            f.write(f"\\n=== First Calendar Data ===\\n")
            first_calendar = mcp_server.calendars_data['calendars'][0]
            f.write(json.dumps(first_calendar, indent=2))
            
    print(f"Final results: {rooms_count} rooms, {calendars_count} calendars, {events_count} events")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
