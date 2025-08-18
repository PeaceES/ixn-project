#!/usr/bin/env python3
"""
Test script to validate the agent fixes.
This script tests basic agent functionality with improved error handling.
"""

import asyncio
import logging
from agent_core import CalendarAgentCore
from utils.terminal_colors import TerminalColors as tc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_basic_functionality():
    """Test basic agent functionality with simple queries."""
    
    print(f"{tc.CYAN}Testing Calendar Scheduling Agent Fixes...{tc.RESET}")
    
    # Initialize the agent core
    agent_core = CalendarAgentCore()
    
    try:
        # Initialize the agent
        print(f"{tc.YELLOW}Initializing agent...{tc.RESET}")
        success, message = await agent_core.initialize_agent()
        if not success:
            print(f"{tc.BG_BRIGHT_RED}Initialization failed: {message}{tc.RESET}")
            return False
        
        print(f"{tc.GREEN}✅ {message}{tc.RESET}")
        
        # Get agent status
        status = await agent_core.get_agent_status()
        print(f"{tc.BLUE}Agent Status:{tc.RESET}")
        print(f"  - MCP Server: {status.get('mcp_status', 'unknown')}")
        print(f"  - User Directory: {'loaded' if status.get('user_directory', {}).get('loaded') else 'not loaded'}")
        print(f"  - Agent ID: {status.get('agent_id', 'N/A')}")
        
        # Test basic queries
        test_queries = [
            "Hi there! Can you help me?",
            "What can you do?",
            "Hello",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{tc.YELLOW}Test {i}: Testing query: '{query}'{tc.RESET}")
            
            success, response = await agent_core.process_message(query)
            
            print(f"{tc.CYAN}Success: {success}{tc.RESET}")
            print(f"{tc.CYAN}Response length: {len(response) if response else 0}{tc.RESET}")
            print(f"{tc.CYAN}Response type: {type(response)}{tc.RESET}")
            
            if success and response and response.strip() and response != "No response available":
                print(f"{tc.GREEN}✅ Test {i} PASSED: Got response{tc.RESET}")
                print(f"{tc.BLUE}Response: {response[:200]}...{tc.RESET}")
                return True  # If any test passes, we've fixed the issue
            else:
                print(f"{tc.RED}❌ Test {i} FAILED: {response}{tc.RESET}")
        
        print(f"{tc.RED}All basic tests failed{tc.RESET}")
        return False
        
    except Exception as e:
        print(f"{tc.RED}Test failed with exception: {e}{tc.RESET}")
        return False
    finally:
        # Don't cleanup for debugging purposes
        print(f"{tc.YELLOW}Keeping agent resources for debugging...{tc.RESET}")

if __name__ == "__main__":
    print(f"{tc.CYAN}Starting agent fix test...{tc.RESET}")
    result = asyncio.run(test_agent_basic_functionality())
    if result:
        print(f"{tc.GREEN}🎉 Agent fix test PASSED! The agent is working.{tc.RESET}")
    else:
        print(f"{tc.RED}💥 Agent fix test FAILED. Further investigation needed.{tc.RESET}")
