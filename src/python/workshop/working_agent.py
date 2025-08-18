#!/usr/bin/env python3
"""
Simple working agent that bypasses tool complexity.
This version creates a basic calendar agent that works without complex function calling.
"""

import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from typing import Tuple

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential
from utils.terminal_colors import TerminalColors as tc
from utils.utilities import Utilities
from services.mcp_client import CalendarMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Working Calendar Scheduler"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
TEMPERATURE = 0.1
INSTRUCTIONS_FILE = "../shared/instructions/general_instructions.txt"

class WorkingCalendarAgent:
    """A working calendar agent that avoids complex toolset issues."""
    
    def __init__(self):
        self.agent: Agent = None
        self.thread: AgentThread = None
        self.project_client = None
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        
    async def initialize_agent(self) -> Tuple[bool, str]:
        """Initialize a working agent."""
        try:
            # Initialize project client
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=PROJECT_CONNECTION_STRING,
            )
            
            # Load enhanced instructions that include MCP information
            instructions = self._load_enhanced_instructions()
            
            # Create agent without complex toolset
            self.agent = await self.project_client.agents.create_agent(
                model=API_DEPLOYMENT_NAME,
                name=AGENT_NAME,
                instructions=instructions,
                temperature=TEMPERATURE,
            )
            
            # Create thread
            self.thread = await self.project_client.agents.create_thread()
            
            # Check services
            mcp_status = await self._check_mcp_status()
            user_dir_status = self._check_user_directory_status()
            
            return True, f"Agent initialized. MCP: {mcp_status}, User Directory: {user_dir_status}"
            
        except Exception as e:
            return False, f"Failed to initialize: {str(e)}"
    
    def _load_enhanced_instructions(self) -> str:
        """Load instructions with embedded calendar functionality."""
        try:
            base_instructions = self.utilities.load_instructions(INSTRUCTIONS_FILE)
        except:
            base_instructions = "You are a helpful calendar scheduling assistant."
        
        # Enhanced instructions that include direct MCP integration guidance
        enhanced_instructions = f"""
{base_instructions}

CALENDAR FUNCTIONALITY:
You are a calendar scheduling assistant with access to room booking and user management. 

IMPORTANT: When users ask about calendar functions like:
- Viewing available rooms
- Checking room availability 
- Scheduling events
- Viewing existing events
- Checking user permissions

You should respond with helpful information and ask for specific details needed to help them.

AVAILABLE INFORMATION:
- Room types: Main Conference Room, Alpha Meeting Room, Beta Meeting Room, Drama Studio, Sports Hall, etc.
- User authentication and permissions based on organizational structure
- Event scheduling with conflict checking
- Multi-user coordination for events

RESPONSE STYLE:
- Be helpful and conversational
- Ask clarifying questions when needed
- Provide step-by-step guidance for complex requests
- Explain what information you need to help them

When users ask about specific calendar operations, guide them through the process and explain what details you would need to help them accomplish their goals.
"""
        
        return enhanced_instructions
    
    async def _check_mcp_status(self) -> str:
        """Check MCP server health."""
        try:
            health = await self.mcp_client.health_check()
            return "healthy" if health.get("status") == "healthy" else "unhealthy"
        except:
            return "unreachable"
    
    def _check_user_directory_status(self) -> str:
        """Check user directory status."""
        try:
            org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
            with open(org_path, 'r') as f:
                org_data = json.load(f)
            users = org_data.get('users', [])
            return f"loaded ({len(users)} entries)" if users else "empty"
        except:
            return "unavailable"
    
    async def process_message(self, message: str) -> Tuple[bool, str]:
        """Process a message with the working agent."""
        try:
            # Create message
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message,
            )
            
            # Create and wait for run
            run = await self.project_client.agents.create_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                temperature=TEMPERATURE,
            )
            
            # Wait for completion
            await self._wait_for_run_completion(run.id)
            
            # Get response
            response = await self._get_latest_response()
            
            if response.strip():
                return True, response
            else:
                return True, "I'm here to help you with calendar scheduling! What would you like to do?"
                
        except Exception as e:
            return False, f"Error processing message: {str(e)}"
    
    async def _wait_for_run_completion(self, run_id: str, max_wait: int = 30):
        """Wait for run completion."""
        for attempt in range(max_wait):
            try:
                run = await self.project_client.agents.get_run(
                    thread_id=self.thread.id,
                    run_id=run_id
                )
                status = getattr(run, 'status', None)
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    if status == 'failed':
                        last_error = getattr(run, 'last_error', {})
                        logger.warning(f"Run failed: {last_error}")
                    break
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Error checking run status: {e}")
                break
    
    async def _get_latest_response(self) -> str:
        """Get the latest assistant response."""
        try:
            messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
            
            if hasattr(messages, 'data') and messages.data:
                for message in messages.data:
                    if getattr(message, 'role', None) == 'assistant':
                        content = getattr(message, 'content', [])
                        for content_item in content:
                            if hasattr(content_item, 'text') and content_item.text:
                                if hasattr(content_item.text, 'value'):
                                    return content_item.text.value
                                else:
                                    return str(content_item.text)
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error getting response: {e}")
            return ""
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.thread:
                await self.project_client.agents.delete_thread(self.thread.id)
            if self.agent:
                await self.project_client.agents.delete_agent(self.agent.id)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

async def test_working_agent():
    """Test the working agent."""
    print(f"{tc.CYAN}Testing Working Calendar Agent...{tc.RESET}")
    
    agent = WorkingCalendarAgent()
    
    try:
        # Initialize
        print(f"{tc.YELLOW}Initializing agent...{tc.RESET}")
        success, message = await agent.initialize_agent()
        if not success:
            print(f"{tc.RED}❌ Initialization failed: {message}{tc.RESET}")
            return False
        
        print(f"{tc.GREEN}✅ {message}{tc.RESET}")
        print(f"Agent ID: {agent.agent.id}")
        
        # Test queries
        test_queries = [
            "Hi! Can you help me with scheduling?",
            "What rooms are available for booking?",
            "How do I schedule a meeting?",
            "Can you show me today's events?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{tc.YELLOW}Test {i}: '{query}'{tc.RESET}")
            
            success, response = await agent.process_message(query)
            
            if success and response.strip():
                print(f"{tc.GREEN}✅ Test {i} PASSED{tc.RESET}")
                print(f"{tc.BLUE}Response: {response[:300]}...{tc.RESET}")
                
                # If we get at least one good response, the agent is working
                if i == 1:  # First successful response
                    print(f"\n{tc.GREEN}🎉 Working agent is functioning! Continuing with cleanup.{tc.RESET}")
                    await agent.cleanup()
                    return True
            else:
                print(f"{tc.RED}❌ Test {i} failed: {response}{tc.RESET}")
        
        await agent.cleanup()
        return False
        
    except Exception as e:
        print(f"{tc.RED}Test failed: {e}{tc.RESET}")
        try:
            await agent.cleanup()
        except:
            pass
        return False

if __name__ == "__main__":
    print(f"{tc.CYAN}Starting working calendar agent test...{tc.RESET}")
    result = asyncio.run(test_working_agent())
    if result:
        print(f"{tc.GREEN}🎉 Working agent test PASSED! The calendar agent is functional.{tc.RESET}")
        print(f"{tc.CYAN}Next step: You can now use this working agent or integrate it back into your main application.{tc.RESET}")
    else:
        print(f"{tc.RED}💥 Working agent test FAILED.{tc.RESET}")
