#!/usr/bin/env python3
"""
Test script to verify agent tool call fixes.
"""

import asyncio
import sys
import os
sys.path.append('/workspaces/build-your-first-agent-with-azure-ai-agent-service-workshop/src/python/workshop')

from src.python.workshop.agent_core import CalendarAgentCore

async def test_agent():
    """Test the agent with a booking request that requires multiple tool calls."""
    
    agent = CalendarAgentCore()
    
    try:
        # Initialize the agent
        success, message = await agent.initialize_agent()
        if not success:
            print(f"❌ Agent initialization failed: {message}")
            return False
            
        print(f"✅ Agent initialized successfully")
        print(f"📋 Status: {message}")
        
        # Test the booking request that was failing
        test_message = "can i book a room for 14th of august in any room, organiser alice chen, time 3pm to 4pm"
        
        print(f"\n🧪 Testing with message: {test_message}")
        
        success, response = await agent.process_message(test_message)
        
        if success:
            print(f"✅ Message processed successfully")
            print(f"📄 Response: {response}")
            return True
        else:
            print(f"❌ Message processing failed: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            await agent.cleanup()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_agent())
    sys.exit(0 if success else 1)
