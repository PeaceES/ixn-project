#!/usr/bin/env python3
"""
Test script to verify HTTP session cleanup is working properly.
This should prevent the "Unclosed client session" errors.
"""
import asyncio
import logging
import sys
import os
import warnings

# Direct import since we're in the workshop directory
from agent_core import CalendarAgentCore

# Set up logging to see HTTP session warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Also capture warnings (including aiohttp warnings)
warnings.filterwarnings("error", category=ResourceWarning)

async def test_http_cleanup():
    """Test that HTTP sessions are properly cleaned up."""
    logger.info("=== HTTP Session Cleanup Test ===")
    
    try:
        # Test 1: Create and cleanup agent normally
        logger.info("Test 1: Normal agent creation and cleanup")
        agent = CalendarAgentCore()
        
        # Test MCP client health check (creates HTTP session)
        health = await agent.mcp_client.health_check()
        logger.info(f"MCP health check result: {health}")
        
        # Properly cleanup
        await agent.cleanup()
        logger.info("✅ Test 1 PASSED: Normal cleanup completed")
        
        # Test 2: Multiple MCP operations then cleanup
        logger.info("\nTest 2: Multiple MCP operations then cleanup")
        agent2 = CalendarAgentCore()
        
        # Multiple operations that create HTTP sessions
        health = await agent2.mcp_client.health_check()
        rooms = await agent2.mcp_client.get_rooms_via_mcp()
        events = await agent2.mcp_client.list_events_via_mcp("all")
        
        logger.info(f"Operations completed - Health: {health.get('status')}")
        logger.info(f"Rooms result: {rooms.get('success', 'error')}")
        logger.info(f"Events result: {events.get('success', 'error')}")
        
        # Cleanup
        await agent2.cleanup()
        logger.info("✅ Test 2 PASSED: Multiple operations cleanup completed")
        
        # Test 3: Test context manager style cleanup
        logger.info("\nTest 3: Context manager style cleanup")
        async with CalendarAgentCore().mcp_client as mcp:
            health = await mcp.health_check()
            logger.info(f"Context manager health check: {health}")
        logger.info("✅ Test 3 PASSED: Context manager cleanup completed")
        
        # Test 4: Force garbage collection to trigger destructors
        logger.info("\nTest 4: Garbage collection test")
        import gc
        
        # Create agent and let it go out of scope
        def create_temp_agent():
            temp_agent = CalendarAgentCore()
            return temp_agent.mcp_client.health_check()
        
        await create_temp_agent()
        
        # Force garbage collection
        gc.collect()
        logger.info("✅ Test 4 PASSED: Garbage collection completed")
        
        logger.info("\n🎉 All HTTP cleanup tests PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ HTTP cleanup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        try:
            # Run the test
            success = await test_http_cleanup()
            
            # Give a moment for any async cleanup to complete
            await asyncio.sleep(0.1)
            
            if success:
                print("\n✅ HTTP session cleanup test PASSED - No unclosed session errors should appear")
                return 0
            else:
                print("\n❌ HTTP session cleanup test FAILED")
                return 1
                
        except Exception as e:
            print(f"\n💥 Test crashed: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    exit_code = asyncio.run(main())
    exit(exit_code)
