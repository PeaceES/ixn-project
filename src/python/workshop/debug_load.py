#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services.calendar_mcp_server import (
    load_rooms, load_calendars, load_events, load_user_directory,
    rooms_data, calendars_data, events_data, user_directory
)

async def test():
    try:
        # Load rooms first
        await load_rooms()
        rooms_count = len(rooms_data.get('rooms', []))
        
        # Load calendars (depends on rooms)
        await load_calendars()
        calendars_count = len(calendars_data.get('calendars', []))
        
        # Load events
        await load_events()
        events_count = len(events_data.get('events', []))
        
        # Load user directory
        await load_user_directory()
        users_count = len(user_directory)
        
        with open('debug_load.txt', 'w') as f:
            f.write("=== Load Functions Debug ===\\n")
            f.write(f"Rooms loaded: {rooms_count}\\n")
            f.write(f"Calendars created: {calendars_count}\\n")
            f.write(f"Events loaded: {events_count}\\n")
            f.write(f"Users loaded: {users_count}\\n")
            
            if rooms_count > 0:
                f.write(f"\\n=== First Room ===\\n")
                first_room = rooms_data['rooms'][0]
                f.write(json.dumps(first_room, indent=2))
                
            if calendars_count > 0:
                f.write(f"\\n=== First Calendar ===\\n")
                first_calendar = calendars_data['calendars'][0]
                f.write(json.dumps(first_calendar, indent=2))
                
        print(f"RESULTS: {rooms_count} rooms, {calendars_count} calendars, {events_count} events, {users_count} users")
        
    except Exception as e:
        with open('debug_load.txt', 'w') as f:
            f.write(f"ERROR: {str(e)}\\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())
