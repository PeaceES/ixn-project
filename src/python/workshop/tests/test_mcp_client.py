#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mcp_client import CalendarMCPClient

async def test_mcp_client():
    client = CalendarMCPClient()
    
    # Test health check
    print("Testing health check...")
    health = await client.health_check()
    print(f"Health: {health}")
    
    if health.get("status") == "healthy":
        print("\nTesting event creation...")
        result = await client.create_event_via_mcp(
            user_id="peace doe",
            calendar_id="central-lecture-hall-main",
            title="Competition rehearsal",
            start_time="2025-07-16T10:00:00Z",
            end_time="2025-07-16T12:00:00Z",
            description=""
        )
        print(f"Create event result: {result}")
    else:
        print("Server not healthy, cannot test event creation")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
