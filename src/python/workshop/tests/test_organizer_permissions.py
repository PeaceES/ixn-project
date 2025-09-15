#!/usr/bin/env python3
"""
Test script to verify organizer-only permissions for event modifications.
This test creates events and verifies that only the original organizer can modify/delete them.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mcp_client import CalendarMCPClient
import json
from datetime import datetime, timedelta

async def test_organizer_permissions():
    """Test that only event organizers can modify/delete their events."""
    client = CalendarMCPClient()
    
    print("=== Testing Organizer-Only Permissions ===\n")
    
    # Test health check first
    print("1. Checking MCP server health...")
    health = await client.health_check()
    print(f"   Health status: {health.get('status', 'unknown')}")
    
    if health.get("status") != "healthy":
        print("   ❌ MCP server not healthy, cannot run tests")
        return False
    
    # Test users - use actual users from org structure
    user1_email = "peaceselem@gmail.com"  # Original organizer (Allison Hill)
    user2_email = "davisjesse@example.net"  # Different user (Angie Henderson) - should be denied
    room_id = "central-lecture-hall-main"
    
    # Create a test event as user1
    print(f"\n2. Creating test event as {user1_email}...")
    now = datetime.now()
    start_time = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    end_time = (now + timedelta(days=1, hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
    
    create_result = await client.create_event_via_mcp(
        user_id=user1_email,
        calendar_id=room_id,
        title="Test Event for Permission Check",
        start_time=start_time,
        end_time=end_time,
        description="Testing organizer permissions"
    )
    
    if not create_result.get("success", False):
        print(f"   ❌ Failed to create test event: {create_result.get('error', 'Unknown error')}")
        return False
    
    event_id = create_result.get("event", {}).get("id")
    if not event_id:
        print("   ❌ No event ID returned from creation")
        return False
    
    print(f"   ✅ Event created successfully with ID: {event_id}")
    
    # Test 3: Try to modify event as the original organizer (should succeed)
    print(f"\n3. Testing modification by original organizer ({user1_email})...")
    modify_result = await client.update_event(
        calendar_id=room_id,
        event_id=event_id,
        user_id=user1_email,
        title="Modified Test Event"
    )
    
    if modify_result.get("success", False):
        print("   ✅ Original organizer can modify their event")
    else:
        print(f"   ❌ Original organizer cannot modify their event: {modify_result.get('error', 'Unknown error')}")
        return False
    
    # Test 4: Try to modify event as a different user (should fail)
    print(f"\n4. Testing modification by different user ({user2_email})...")
    unauthorized_modify = await client.update_event(
        calendar_id=room_id,
        event_id=event_id,
        user_id=user2_email,
        title="Unauthorized Modification Attempt"
    )
    
    if not unauthorized_modify.get("success", False):
        error_msg = unauthorized_modify.get("error", "")
        if "Access denied" in error_msg or "Permission denied" in error_msg:
            print("   ✅ Different user correctly denied modification access")
        else:
            print(f"   ⚠️  Different user denied, but unexpected error: {error_msg}")
    else:
        print("   ❌ Different user was incorrectly allowed to modify the event")
        return False
    
    # Test 5: Try to delete event as a different user (should fail)
    print(f"\n5. Testing deletion by different user ({user2_email})...")
    unauthorized_delete = await client.delete_event_via_mcp(
        calendar_id=room_id,
        event_id=event_id,
        user_id=user2_email
    )
    
    if not unauthorized_delete.get("success", False):
        error_msg = unauthorized_delete.get("error", "")
        if "Access denied" in error_msg or "Permission denied" in error_msg:
            print("   ✅ Different user correctly denied deletion access")
        else:
            print(f"   ⚠️  Different user denied, but unexpected error: {error_msg}")
    else:
        print("   ❌ Different user was incorrectly allowed to delete the event")
        return False
    
    # Test 6: Try to delete event as the original organizer (should succeed)
    print(f"\n6. Testing deletion by original organizer ({user1_email})...")
    delete_result = await client.delete_event_via_mcp(
        calendar_id=room_id,
        event_id=event_id,
        user_id=user1_email
    )
    
    if delete_result.get("success", False):
        print("   ✅ Original organizer can delete their event")
    else:
        print(f"   ❌ Original organizer cannot delete their event: {delete_result.get('error', 'Unknown error')}")
        return False
    
    print("\n=== All Permission Tests Passed! ===")
    print("✅ Organizer-only permissions are working correctly:")
    print("   - Only original organizers can modify their events")
    print("   - Only original organizers can delete their events")
    print("   - Other users are properly denied access")
    
    return True

async def test_terminal_user_id_requirement():
    """Test that agent core functions require user_id when no default context is set."""
    print("\n=== Testing Terminal Interface User ID Requirements ===\n")
    
    # Import agent core without setting environment variables (simulating terminal usage)
    from agent_core import CalendarAgentCore
    
    # Create agent core without user context (terminal mode)
    agent = CalendarAgentCore(enable_tools=True)
    
    # These should all fail and ask for user ID
    test_event_id = "dummy-event-id"
    
    print("1. Testing reschedule_event_via_mcp without user_id...")
    result = await agent.reschedule_event_via_mcp(
        event_id=test_event_id,
        new_start_time="2025-07-16T14:00:00Z",
        new_end_time="2025-07-16T16:00:00Z"
    )
    result_data = json.loads(result)
    if result_data.get("success") == False and ("User identification required" in result_data.get("error", "") or "User identification required" in result_data.get("message", "")):
        print("   ✅ Correctly requires user ID for rescheduling")
    else:
        print(f"   ❌ Did not require user ID: {result}")
        return False
    
    print("2. Testing modify_event_via_mcp without user_id...")
    result = await agent.modify_event_via_mcp(
        event_id=test_event_id,
        title="Modified Title"
    )
    result_data = json.loads(result)
    if result_data.get("success") == False and ("User identification required" in result_data.get("error", "") or "User identification required" in result_data.get("message", "")):
        print("   ✅ Correctly requires user ID for modification")
    else:
        print(f"   ❌ Did not require user ID: {result}")
        return False
    
    print("3. Testing cancel_event_via_mcp without user_id...")
    result = await agent.cancel_event_via_mcp(event_id=test_event_id)
    result_data = json.loads(result)
    if result_data.get("success") == False and ("User identification required" in result_data.get("error", "") or "User identification required" in result_data.get("message", "")):
        print("   ✅ Correctly requires user ID for cancellation")
    else:
        print(f"   ❌ Did not require user ID: {result}")
        return False
    
    print("\n✅ Terminal interface correctly requires user ID for all modification operations")
    return True

if __name__ == "__main__":
    async def run_all_tests():
        print("Starting organizer permission tests...\n")
        
        # Test MCP server permissions
        server_test_passed = await test_organizer_permissions()
        
        # Test terminal interface requirements
        terminal_test_passed = await test_terminal_user_id_requirement()
        
        print(f"\n=== Final Results ===")
        print(f"MCP Server Permissions: {'✅ PASSED' if server_test_passed else '❌ FAILED'}")
        print(f"Terminal User ID Requirements: {'✅ PASSED' if terminal_test_passed else '❌ FAILED'}")
        
        if server_test_passed and terminal_test_passed:
            print("\n🎉 All tests passed! Organizer-only permissions are working correctly.")
            return True
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            return False
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
