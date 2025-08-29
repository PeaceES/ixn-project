"""
Terminal interface for the Calendar Scheduling Agent.
This is the original terminal-based interface, now using the shared agent_core module.
"""

import asyncio
import logging
from dotenv import load_dotenv

from agent_core import CalendarAgentCore
from utils.terminal_colors import TerminalColors as tc

# Configure logging to show debug-level agent diagnostics for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('azure.ai.projects').setLevel(logging.WARNING)
logging.getLogger('evaluation.working_evaluator').setLevel(logging.WARNING)

load_dotenv()


async def main() -> None:
    """
    Example questions for the Calendar Scheduling Agent:
    - "Show me all available rooms"
    - "Check if the Main Conference Room is available tomorrow at 2pm"
    - "Schedule a meeting in the Alpha Meeting Room for tomorrow at 3pm"
    - "I want to book the Drama Studio for a rehearsal next Friday"
    - "What events are scheduled for this week?"
    
    Note: Microsoft Documentation Search functionality has been removed from this agent.
    The Microsoft Docs MCP server is available as a submodule for reference if needed.
    """
    
    # Initialize the agent core
    # Start in functions-only mode: enable functions but keep Code Interpreter disabled
    agent_core = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    print(f"{tc.CYAN}Starting Calendar Scheduling Agent...{tc.RESET}")
    
    # Initialize the agent
    success, message = await agent_core.initialize_agent()
    if not success:
        print(f"{tc.BG_BRIGHT_RED}Initialization failed: {message}{tc.RESET}")
        print("Exiting...")
        return
    
    print(f"{tc.GREEN}✅ {message}{tc.RESET}")
    
    # Get agent status for display
    status = await agent_core.get_agent_status()
    print(f"{tc.BLUE}Agent Status:{tc.RESET}")
    print(f"  - MCP Server: {status.get('mcp_status', 'unknown')}")
    print(f"  - User Directory: {'loaded' if status.get('user_directory', {}).get('loaded') else 'not loaded'}")
    print(f"  - Agent ID: {status.get('agent_id', 'N/A')}")
    
    cmd = None
    
    while True:
        prompt = input(
            f"\n\n{tc.GREEN}Enter your query (type exit or save to finish): {tc.RESET}"
        ).strip()
        
        if not prompt:
            continue
        
        cmd = prompt.lower()
        if cmd in {"exit", "save"}:
            break
        
        # Process the message
        print(f"{tc.YELLOW}Processing your request...{tc.RESET}")
        success, response = await agent_core.process_message(prompt)
        print(f"{tc.BLUE}Raw response: {response}{tc.RESET}")
        print(f"{tc.CYAN}Response type: {type(response)}{tc.RESET}")
        print(f"{tc.CYAN}Response repr: {repr(response)}{tc.RESET}")
        if not success:
            print(f"{tc.RED}Error: {response}{tc.RESET}")
        else:
            print(f"{tc.GREEN}Agent response: {response}{tc.RESET}")
    
    # Handle cleanup
    if cmd == "save":
        print(f"{tc.CYAN}The agent has not been deleted, so you can continue experimenting with it in the Azure AI Foundry.{tc.RESET}")
        print(f"Navigate to https://ai.azure.com, select your project, then playgrounds, agents playground, then select agent id: {status.get('agent_id', 'N/A')}")
    else:
        print(f"{tc.YELLOW}Cleaning up agent resources...{tc.RESET}")
        await agent_core.cleanup()
        print(f"{tc.GREEN}✅ Agent resources have been cleaned up.{tc.RESET}")


if __name__ == "__main__":
    print(f"{tc.CYAN}Starting async program...{tc.RESET}")
    asyncio.run(main())
    print(f"{tc.CYAN}Program finished.{tc.RESET}")
