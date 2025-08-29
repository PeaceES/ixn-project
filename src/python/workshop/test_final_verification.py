#!/usr/bin/env python3
"""Final test to verify schedule_event_with_permissions is working correctly"""

import asyncio
import json
from agent_core import CalendarAgentCore

async def test_all_scenarios():
    """Test various booking scenarios"""
    
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    # First, get available rooms to use valid room IDs
    print("=== Getting available rooms ===")
    rooms_result = await agent.get_rooms_via_mcp()
    rooms_data = json.loads(rooms_result)
    if rooms_data.get("success"):
        print(f"Found {len(rooms_data.get('calendars', []))} rooms")
        # Print first 3 rooms for reference
        for room in rooms_data.get('calendars', [])[:3]:
            print(f"  - {room['id']}: {room['name']}")
    
    print("\n=== Test 1: Department booking (should succeed) ===")
    result = await agent.schedule_event_with_permissions(
        user_id="5",
        entity_type="department",
        entity_name="Computing Department",
        room_id="central-lecture-hall-main",  # Using a valid room ID
        title="Department Strategy Meeting",
        start_time="2025-09-01T10:00:00Z",
        end_time="2025-09-01T11:00:00Z",
        description="Quarterly planning"
    )
    print_result(result)
    
    print("\n=== Test 2: Course booking (should succeed) ===")
    result = await agent.schedule_event_with_permissions(
        user_id="5",
        entity_type="course",
        entity_name="Computer Science",
        room_id="computing-lab-201",  # Using a computing lab
        title="CS201 Lab Session",
        start_time="2025-09-02T14:00:00Z",
        end_time="2025-09-02T16:00:00Z",
        description="Programming lab"
    )
    print_result(result)
    
    print("\n=== Test 3: Society booking (should succeed) ===")
    result = await agent.schedule_event_with_permissions(
        user_id="5",
        entity_type="society",
        entity_name="AI Society",
        room_id="central-seminar-room-b",  # Using a seminar room
        title="AI Society Workshop",
        start_time="2025-09-03T17:00:00Z",
        end_time="2025-09-03T19:00:00Z",
        description="Introduction to Machine Learning"
    )
    print_result(result)
    
    print("\n=== Test 4: Wrong department (should fail with permission denied) ===")
    result = await agent.schedule_event_with_permissions(
        user_id="5",
        entity_type="department",
        entity_name="Engineering Department",  # User 5 is not in Engineering
        room_id="central-lecture-hall-main",
        title="Engineering Meeting",
        start_time="2025-09-04T10:00:00Z",
        end_time="2025-09-04T11:00:00Z",
        description="Should fail"
    )
    print_result(result)
    
    print("\n=== Test 5: Society officer booking (should succeed only for their society) ===")
    # User 17 (Matthew Porter) is an officer of Drama Society
    result = await agent.schedule_event_with_permissions(
        user_id="17",
        entity_type="society",
        entity_name="Drama Society",
        room_id="arts-theatre",
        title="Drama Rehearsal",
        start_time="2025-09-05T18:00:00Z",
        end_time="2025-09-05T20:00:00Z",
        description="Play rehearsal"
    )
    print_result(result)
    
    await agent.cleanup()

def print_result(result: str):
    """Pretty print the result"""
    try:
        data = json.loads(result)
        if data.get("success"):
            print(f"✅ SUCCESS: {data.get('message', 'Event scheduled')}")
            if data.get("event"):
                print(f"   Event ID: {data['event']['id']}")
                print(f"   Title: {data['event']['title']}")
                print(f"   Room: {data['event']['calendar_name']}")
        else:
            print(f"❌ FAILED: {data.get('message', data.get('error', 'Unknown error'))}")
            if data.get("allowed_entities"):
                print("   User can book for:")
                for entity in data["allowed_entities"]:
                    print(f"     - {entity['type']}: {entity['name']}")
    except Exception as e:
        print(f"❌ ERROR parsing result: {e}")
        print(f"   Raw result: {result}")

if __name__ == "__main__":
    asyncio.run(test_all_scenarios())
