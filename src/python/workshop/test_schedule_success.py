#!/usr/bin/env python3
"""Test script to demonstrate successful booking with correct permissions"""

import asyncio
import json
from agent_core import CalendarAgentCore

async def test_successful_booking():
    """Test schedule_event_with_permissions with correct permissions"""
    
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    print("=== Testing successful booking with correct permissions ===\n")
    
    # User 5 can book for Computing Department (id: 2)
    test_params = {
        "user_id": "5",
        "entity_type": "department", 
        "entity_name": "Computing Department",  # Changed from Engineering to Computing
        "room_id": "central-lecture-hall-main",  # Using a valid room ID
        "title": "Department Meeting",
        "start_time": "2025-08-30T14:00:00Z",
        "end_time": "2025-08-30T15:00:00Z",
        "description": "Monthly department meeting"
    }
    
    print("Test parameters:")
    print(json.dumps(test_params, indent=2))
    
    # First check what user 5 can book for
    print("\n1. Checking user's booking permissions...")
    entities_result = await agent.get_user_booking_entity(test_params["user_id"])
    entities_data = json.loads(entities_result)
    print(f"\nUser can book for:")
    for entity in entities_data.get("entities", []):
        print(f"  - {entity['type']}: {entity['name']}")
    
    # Now try to schedule the event
    print("\n2. Scheduling event with permissions...")
    result = await agent.schedule_event_with_permissions(**test_params)
    result_data = json.loads(result)
    
    print(f"\nResult:")
    print(json.dumps(result_data, indent=2))
    
    if result_data.get("success"):
        print("\n✅ SUCCESS: Event scheduled successfully!")
    else:
        print(f"\n❌ FAILED: {result_data.get('message', 'Unknown error')}")
    
    # Also test booking for a course in the user's department
    print("\n\n=== Testing booking for a course ===")
    course_params = {
        "user_id": "5",
        "entity_type": "course",
        "entity_name": "Computer Science",  # A course in Computing Department
        "room_id": "eng-lab-101",
        "title": "CS101 Lecture", 
        "start_time": "2025-08-31T09:00:00Z",
        "end_time": "2025-08-31T10:30:00Z",
        "description": "Introduction to Programming"
    }
    
    print("Test parameters:")
    print(json.dumps(course_params, indent=2))
    
    result2 = await agent.schedule_event_with_permissions(**course_params)
    result2_data = json.loads(result2)
    
    print(f"\nResult:")
    print(json.dumps(result2_data, indent=2))
    
    if result2_data.get("success"):
        print("\n✅ SUCCESS: Course event scheduled successfully!")
    else:
        print(f"\n❌ FAILED: {result2_data.get('message', 'Unknown error')}")
    
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_successful_booking())
