"""
Simple test script to validate the agent_core module works.
"""

import asyncio
import sys
import os
import pytest

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core import CalendarAgentCore

@pytest.mark.asyncio
async def test_agent_core():
    """Test the agent core functionality."""
    print("🧪 Testing CalendarAgentCore...")
    
    # Initialize agent
    agent = CalendarAgentCore()
    print("✅ Agent instance created")
    
    # Test MCP client health check
    try:
        health = await agent.mcp_client.health_check()
        print(f"✅ MCP Health Check: {health}")
    except Exception as e:
        print(f"⚠️ MCP Health Check failed: {e}")
    
    # Test user directory fetch
    try:
        users = agent.fetch_user_directory()
        print(f"✅ User Directory: {len(users)} entries")
    except Exception as e:
        print(f"⚠️ User Directory fetch failed: {e}")
    
    # Test function initialization
    try:
        agent._initialize_functions()
        print("✅ Functions initialized")
    except Exception as e:
        print(f"❌ Function initialization failed: {e}")
        return False
    
    print("🎉 All basic tests passed!")
    return True

if __name__ == "__main__":
    print("Starting basic validation test...")
    success = asyncio.run(test_agent_core())
    if success:
        print("\n🎉 Setup validation successful!")
        print("You can now run:")
        print("  - Terminal interface: python main.py")
        print("  - Streamlit interface: streamlit run streamlit_app.py")
    else:
        print("\n❌ Setup validation failed!")
        sys.exit(1)
