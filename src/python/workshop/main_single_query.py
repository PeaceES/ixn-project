"""
Single-query version of the Calendar Scheduling Agent for subprocess usage.
This version processes one query and exits, perfect for Streamlit subprocess calls.
"""

import asyncio
import logging
import sys
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


async def process_single_query() -> None:
    """
    Process a single query from stdin and exit.
    Perfect for subprocess calls from Streamlit.
    """
    
    print("DEBUG: Starting process_single_query")
    
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
        
        print("DEBUG: Reading query from stdin...")
        # Read query from stdin (sent by Streamlit)
        query = input().strip()
        print(f"DEBUG: Received query: '{query}'")
        
        if not query or query.lower() in {"exit", "save"}:
            print("No query provided")
            return
        
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
    asyncio.run(process_single_query())
    print("DEBUG: Script finished")
