#!/usr/bin/env python3
"""Test script to debug schedule_event_with_permissions function"""

import asyncio
import json
import logging
from agent_core import CalendarAgentCore

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_schedule_event_with_permissions():
    """Test the schedule_event_with_permissions function directly"""
    
    # Create agent core instance
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    print("=== Testing schedule_event_with_permissions ===\n")
    
    # Test parameters
    test_params = {
        "user_id": "5",  # Alice Johnson
        "entity_type": "department",
        "entity_name": "Engineering Department",
        "room_id": "room_1",
        "title": "Test Meeting",
        "start_time": "2025-08-30T10:00:00Z",
        "end_time": "2025-08-30T11:00:00Z",
        "description": "Test meeting description"
    }
    
    print(f"Test parameters: {json.dumps(test_params, indent=2)}\n")
    
    try:
        # First, test get_user_booking_entity to ensure user data is accessible
        print("1. Testing get_user_booking_entity...")
        entities_result = await agent.get_user_booking_entity(test_params["user_id"])
        print(f"User entities result: {entities_result}\n")
        
        # Now test schedule_event_with_permissions
        print("2. Testing schedule_event_with_permissions...")
        result = await agent.schedule_event_with_permissions(
            user_id=test_params["user_id"],
            entity_type=test_params["entity_type"],
            entity_name=test_params["entity_name"],
            room_id=test_params["room_id"],
            title=test_params["title"],
            start_time=test_params["start_time"],
            end_time=test_params["end_time"],
            description=test_params["description"]
        )
        
        print(f"Schedule result: {result}\n")
        
        # Parse and pretty-print the result
        try:
            result_data = json.loads(result)
            print("Parsed result:")
            print(json.dumps(result_data, indent=2))
        except json.JSONDecodeError:
            print("Could not parse result as JSON")
            
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    
    # Cleanup
    await agent.cleanup()

async def test_direct_mcp_call():
    """Test calling MCP client directly to ensure it's working"""
    
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    print("\n=== Testing direct MCP calls ===\n")
    
    try:
        # Test MCP health check
        print("1. Testing MCP health check...")
        health = await agent.mcp_client.health_check()
        print(f"MCP health: {json.dumps(health, indent=2)}\n")
        
        # Test getting rooms
        print("2. Testing get rooms...")
        rooms_result = await agent.get_rooms_via_mcp()
        print(f"Rooms result: {rooms_result[:200]}...\n")
        
    except Exception as e:
        logger.error(f"Error during MCP test: {e}", exc_info=True)
    
    await agent.cleanup()

async def test_org_structure():
    """Test loading org structure to ensure user data is accessible"""
    
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    print("\n=== Testing org structure loading ===\n")
    
    try:
        # Test loading org structure
        print("1. Testing _load_org_structure...")
        org_data = agent._load_org_structure()
        
        if org_data:
            print(f"Loaded org structure with {len(org_data.get('users', []))} users")
            print(f"Departments: {len(org_data.get('departments', []))}")
            print(f"Courses: {len(org_data.get('courses', []))}")
            print(f"Societies: {len(org_data.get('societies', []))}")
            
            # Find user 5 (Alice Johnson)
            users = org_data.get('users', [])
            user_5 = next((u for u in users if u.get('id') == 5), None)
            if user_5:
                print(f"\nUser 5 details: {json.dumps(user_5, indent=2)}")
        else:
            print("Failed to load org structure!")
            
    except Exception as e:
        logger.error(f"Error during org test: {e}", exc_info=True)
    
    await agent.cleanup()

async def main():
    """Run all tests"""
    await test_org_structure()
    await test_direct_mcp_call()
    await test_schedule_event_with_permissions()

if __name__ == "__main__":
    asyncio.run(main())
