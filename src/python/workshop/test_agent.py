"""
Test version of the Calendar Scheduling Agent that doesn't wait for stdin.
"""

import asyncio
import logging
from dotenv import load_dotenv

from agent_core import CalendarAgentCore
from utils.terminal_colors import TerminalColors as tc

# Configure logging to reduce verbosity
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('azure.ai.projects').setLevel(logging.WARNING)
logging.getLogger('evaluation.working_evaluator').setLevel(logging.WARNING)

load_dotenv()


async def test_agent() -> None:
    """
    Test the agent with a simple query.
    """
    
    print("DEBUG: Starting test_agent")
    
    # Initialize the agent core
    agent_core = CalendarAgentCore()
    
    try:
        print("DEBUG: Initializing agent...")
        # Initialize the agent
        success, message = await agent_core.initialize_agent()
        print(f"DEBUG: Agent initialization result: success={success}, message={message}")
        if not success:
            print(f"ERROR: Initialization failed: {message}")
            return
        
        # Use a test query instead of reading from stdin
        query = "Hello, can you help me understand what you can do?"
        print(f"DEBUG: Using test query: '{query}'")
        
        print("DEBUG: Processing message...")
        # Process the message
        success, response = await agent_core.process_message(query, for_streamlit=False)
        print(f"DEBUG: Message processing result: success={success}")
        
        if success:
            # Clean output - remove terminal colors for web display
            clean_response = response.replace(tc.CYAN, "").replace(tc.RESET, "").replace(tc.GREEN, "").replace(tc.RED, "").replace(tc.YELLOW, "").replace(tc.BLUE, "")
            print(f"SUCCESS: {clean_response}")
        else:
            print(f"ERROR: {response}")
            
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("DEBUG: Starting cleanup...")
        # Always cleanup
        try:
            await agent_core.cleanup()
            print("DEBUG: Cleanup completed")
        except Exception as e:
            print(f"CLEANUP_ERROR: {str(e)}")


if __name__ == "__main__":
    print("DEBUG: Script started")
    asyncio.run(test_agent())
    print("DEBUG: Script finished")
