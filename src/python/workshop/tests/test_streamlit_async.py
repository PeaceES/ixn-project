"""
Test script to verify the async agent manager works correctly.
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from streamlit_app import AsyncAgentManager
from agent_core import CalendarAgentCore

async def test_async_operations():
    """Test that async operations work correctly."""
    print("Creating CalendarAgentCore...")
    agent = CalendarAgentCore()
    
    print("Testing get_agent_status...")
    status = await agent.get_agent_status()
    print(f"Status: {status}")
    
    print("✅ Async operations test passed!")

def test_agent_manager():
    """Test the AsyncAgentManager."""
    print("Creating AsyncAgentManager...")
    manager = AsyncAgentManager()
    
    print("Testing run_async method...")
    result = manager.run_async(test_async_operations())
    
    print("Cleaning up...")
    manager.cleanup()
    
    print("✅ AsyncAgentManager test passed!")

if __name__ == "__main__":
    test_agent_manager()
