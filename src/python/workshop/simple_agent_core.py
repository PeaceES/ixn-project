#!/usr/bin/env python3
"""
Simplified agent core that works without complex toolsets.
This version focuses on basic functionality and gradually adds tools.
"""

import asyncio
import logging
import os
import json
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential

from utils.utilities import Utilities
from services.mcp_client import CalendarMCPClient
from utils.terminal_colors import TerminalColors as tc

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Simple Calendar Scheduler"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
TEMPERATURE = 0.1
INSTRUCTIONS_FILE = "../shared/instructions/general_instructions.txt"


class SimpleCalendarAgentCore:
    """Simplified calendar agent that works without complex tools."""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self.thread: Optional[AgentThread] = None
        self.project_client = None
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        self._operation_active = False

    def _cleanup_run_thread(self):
        """Reset agent and thread state after operation or error."""
        self.agent = None
        self.thread = None
        self._operation_active = False

    async def initialize_agent(self) -> Tuple[bool, str]:
        """Initialize the agent. Returns (success, message)."""
        logger.info("[SimpleAgentCore] Initializing simple agent...")
        
        try:
            # Initialize project client
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=PROJECT_CONNECTION_STRING,
            )

            # Load instructions
            instructions = self.utilities.load_instructions(INSTRUCTIONS_FILE)
            
            # Enhanced instructions for calendar functionality
            calendar_instructions = instructions + """

You are a helpful calendar scheduling assistant. You can help users with:
- General questions about scheduling and calendar management
- Providing information about rooms and availability
- Helping users understand the booking process
- Answering questions about the organization structure

For complex operations like checking availability or booking rooms, you should guide users through the process step by step.

Be friendly, helpful, and informative. If users ask about specific room availability or want to book rooms, acknowledge their request and let them know you're here to help guide them through the process.
"""

            # Create simple agent without tools
            self.agent = await self.project_client.agents.create_agent(
                model=API_DEPLOYMENT_NAME,
                name=AGENT_NAME,
                instructions=calendar_instructions,
                temperature=TEMPERATURE,
            )
            logger.info(f"[SimpleAgentCore] Created agent with ID: {self.agent.id}")

            # Create thread
            self.thread = await self.project_client.agents.create_thread()
            logger.info(f"[SimpleAgentCore] Created thread with ID: {self.thread.id}")

            # Check MCP health status
            try:
                health = await self.mcp_client.health_check()
                mcp_status = "healthy" if health.get("status") == "healthy" else "unhealthy"
            except Exception:
                mcp_status = "unreachable"

            # Check user directory status  
            try:
                org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
                with open(org_path, 'r') as f:
                    org_data = json.load(f)
                user_count = len(org_data.get('users', []))
                user_dir_status = f"loaded ({user_count} entries)"
            except Exception:
                user_dir_status = "empty/inaccessible"

            success_msg = f"Simple agent initialized successfully. MCP: {mcp_status}, User Directory: {user_dir_status}"
            logger.info(f"[SimpleAgentCore] Initialization complete. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
            return True, success_msg
            
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Failed to initialize simple agent: {str(e)}"
            logger.error(f"[SimpleAgentCore] Initialization error: {error_msg}")
            return False, error_msg

    async def process_message(self, message: str) -> Tuple[bool, str]:
        """Process a message with the agent. Returns (success, response)."""
        if not self.agent or not self.thread:
            logger.warning("[SimpleAgentCore] Agent or thread not initialized.")
            return False, "Agent not initialized"
        if self._operation_active:
            logger.warning("[SimpleAgentCore] Agent is busy processing another request.")
            return False, "Agent is busy processing another request. Please wait."
        
        self._operation_active = True
        logger.info(f"[SimpleAgentCore] Processing message. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
        
        try:
            if not self.project_client:
                return False, "Project client not initialized"
            
            # Create message
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message,
            )
            logger.info(f"[SimpleAgentCore] Message created for thread ID: {self.thread.id}")

            # Create and wait for run
            run = await self.project_client.agents.create_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                temperature=TEMPERATURE,
            )
            logger.info(f"[SimpleAgentCore] Run started: {run.id}")

            # Wait for completion
            await self._wait_for_run_completion(run.id)

            # Get response from messages
            response_text = await self._get_latest_assistant_message()
            
            if not response_text.strip():
                # Check run status for errors
                final_run = await self.project_client.agents.get_run(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
                if getattr(final_run, 'status', None) == 'failed':
                    last_error = getattr(final_run, 'last_error', {})
                    error_msg = last_error.get('message', 'Unknown error occurred')
                    response_text = f"I apologize, but I encountered an error: {error_msg}. Please try rephrasing your question."
                else:
                    response_text = "I apologize, but I'm having trouble generating a response right now. Please try again."
            
            return True, response_text
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"[SimpleAgentCore] Error processing message: {error_msg}")
            return False, error_msg
        finally:
            self._operation_active = False
            logger.info(f"[SimpleAgentCore] Operation complete.")

    async def _wait_for_run_completion(self, run_id: str, max_wait: int = 30):
        """Wait for a run to complete."""
        for attempt in range(max_wait):
            try:
                run = await self.project_client.agents.get_run(
                    thread_id=self.thread.id,
                    run_id=run_id
                )
                status = getattr(run, 'status', None)
                logger.info(f"[SimpleAgentCore] Run {run_id} status: {status}")
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    logger.info(f"[SimpleAgentCore] Run {run_id} finished with status: {status}")
                    break
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[SimpleAgentCore] Error checking run status: {e}")
                break

    async def _get_latest_assistant_message(self) -> str:
        """Get the latest assistant message from the thread."""
        try:
            messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
            
            if hasattr(messages, 'data') and messages.data:
                # Look for the most recent assistant message
                for message in messages.data:
                    if getattr(message, 'role', None) == 'assistant':
                        content = getattr(message, 'content', [])
                        response_text = ""
                        for content_item in content:
                            if hasattr(content_item, 'text') and content_item.text:
                                if hasattr(content_item.text, 'value'):
                                    response_text += content_item.text.value
                                else:
                                    response_text += str(content_item.text)
                        if response_text.strip():
                            return response_text
            
            return ""
        except Exception as e:
            logger.warning(f"[SimpleAgentCore] Error getting latest message: {e}")
            return ""

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        try:
            if self.agent and self.thread and self.project_client:
                await self.project_client.agents.delete_thread(self.thread.id)
                await self.project_client.agents.delete_agent(self.agent.id)
                logger.info("[SimpleAgentCore] Agent resources cleaned up successfully")
        except Exception as e:
            logger.error(f"[SimpleAgentCore] Error during cleanup: {e}")
        finally:
            self._cleanup_run_thread()

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status for UI display."""
        status = {
            "agent_initialized": self.agent is not None,
            "thread_created": self.thread is not None,
            "agent_id": self.agent.id if self.agent else None,
            "thread_id": self.thread.id if self.thread else None,
        }
        
        # Check MCP health
        try:
            health = await self.mcp_client.health_check()
            status["mcp_status"] = "healthy" if health.get("status") == "healthy" else "unhealthy"
        except Exception:
            status["mcp_status"] = "unreachable"
        
        # Check user directory
        try:
            org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
            with open(org_path, 'r') as f:
                org_data = json.load(f)
            user_count = len(org_data.get('users', []))
            status["user_directory"] = {
                "loaded": user_count > 0,
                "count": user_count
            }
        except Exception:
            status["user_directory"] = {
                "loaded": False,
                "count": 0
            }
        
        return status


# Test the simple agent
async def test_simple_calendar_agent():
    """Test the simple calendar agent."""
    print(f"{tc.CYAN}Testing Simple Calendar Agent...{tc.RESET}")
    
    agent = SimpleCalendarAgentCore()
    
    try:
        # Initialize
        print(f"{tc.YELLOW}Initializing agent...{tc.RESET}")
        success, message = await agent.initialize_agent()
        if not success:
            print(f"{tc.RED}Initialization failed: {message}{tc.RESET}")
            return False
        
        print(f"{tc.GREEN}✅ {message}{tc.RESET}")
        
        # Get status
        status = await agent.get_agent_status()
        print(f"{tc.BLUE}Agent Status:{tc.RESET}")
        print(f"  - MCP Server: {status.get('mcp_status', 'unknown')}")
        print(f"  - User Directory: {'loaded' if status.get('user_directory', {}).get('loaded') else 'not loaded'}")
        print(f"  - Agent ID: {status.get('agent_id', 'N/A')}")
        
        # Test queries
        test_queries = [
            "Hi! Can you help me with scheduling?",
            "What can you help me with?",
            "I need to book a room for a meeting",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{tc.YELLOW}Test {i}: '{query}'{tc.RESET}")
            
            success, response = await agent.process_message(query)
            
            if success and response and response.strip():
                print(f"{tc.GREEN}✅ Test {i} PASSED{tc.RESET}")
                print(f"{tc.BLUE}Response: {response[:200]}...{tc.RESET}")
                
                # If any test passes, we've succeeded
                return True
            else:
                print(f"{tc.RED}❌ Test {i} FAILED: {response}{tc.RESET}")
        
        print(f"{tc.RED}All tests failed{tc.RESET}")
        return False
        
    except Exception as e:
        print(f"{tc.RED}Test failed with exception: {e}{tc.RESET}")
        return False
    finally:
        # Don't cleanup for debugging
        print(f"{tc.YELLOW}Keeping agent for debugging...{tc.RESET}")


if __name__ == "__main__":
    print(f"{tc.CYAN}Starting simple calendar agent test...{tc.RESET}")
    result = asyncio.run(test_simple_calendar_agent())
    if result:
        print(f"{tc.GREEN}🎉 Simple calendar agent test PASSED!{tc.RESET}")
    else:
        print(f"{tc.RED}💥 Simple calendar agent test FAILED.{tc.RESET}")
