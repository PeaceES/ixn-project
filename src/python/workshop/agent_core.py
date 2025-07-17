"""
Core agent functionality for the Calendar Scheduling Agent.
This module contains the reusable agent logic that can be used by both
the terminal interface (main.py) and the Streamlit UI (streamlit_app.py).
"""

import asyncio
import logging
import os
import json
import httpx
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    AsyncFunctionTool,
    AsyncToolSet,
    CodeInterpreterTool,
)
from azure.identity import DefaultAzureCredential

from agent.stream_event_handler import StreamEventHandler
from utils.utilities import Utilities
from services.mcp_client import CalendarMCPClient
from services.microsoft_docs_mcp_client import MicrosoftDocsMCPClient

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Calendar Scheduler"
FONTS_ZIP = "fonts/fonts.zip"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = "../shared/instructions/general_instructions.txt"


class StreamlitEventHandler(StreamEventHandler):
    """Custom event handler for Streamlit that captures responses."""
    
    def __init__(self, functions, project_client, utilities):
        super().__init__(functions, project_client, utilities)
        self.captured_response = ""
        self.response_complete = False
        
    def on_message_delta(self, delta):
        """Capture message deltas for Streamlit display."""
        if hasattr(delta, 'content') and delta.content:
            for content in delta.content:
                if hasattr(content, 'text') and content.text:
                    self.captured_response += content.text.value
        
    def on_message_done(self, message):
        """Mark response as complete."""
        self.response_complete = True
        super().on_message_done(message)


class CalendarAgentCore:
    """Core calendar agent functionality."""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self.thread: Optional[AgentThread] = None
        self.project_client: Optional[AIProjectClient] = None
        self.toolset = AsyncToolSet()
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        self.microsoft_docs_client = MicrosoftDocsMCPClient()
        self.shared_thread_id: Optional[str] = None
        self.functions = None
        self._initialize_functions()
        
    def _initialize_functions(self):
        """Initialize the function tools."""
        self.functions = AsyncFunctionTool([
            self.get_events_via_mcp,
            self.check_room_availability_via_mcp,
            self.get_rooms_via_mcp,
            self.schedule_event_with_organizer,
            self.search_microsoft_documentation,
        ])
    
    async def get_events_via_mcp(self) -> str:
        """Get events via MCP server."""
        try:
            health = await self.mcp_client.health_check()
            if not health.get("status") == "healthy":
                return json.dumps({
                    "success": False,
                    "error": "MCP server not available",
                    "message": "Calendar service is currently unavailable"
                })
            
            result = await self.mcp_client.list_events_via_mcp("all")
            if result.get("success"):
                return json.dumps(result)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"MCP error: {result.get('error')}",
                    "message": "Could not retrieve events"
                })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"MCP connection failed: {e}",
                "message": "Calendar service is currently unavailable"
            })

    async def check_room_availability_via_mcp(self, room_id: str, start_time: str, end_time: str) -> str:
        """Check room availability via MCP server."""
        try:
            health = await self.mcp_client.health_check()
            if not health.get("status") == "healthy":
                return json.dumps({
                    "success": False,
                    "error": "MCP server not available",
                    "message": f"Cannot check availability for room {room_id}"
                })
            
            result = await self.mcp_client.check_room_availability_via_mcp(room_id, start_time, end_time)
            if result.get("success"):
                return json.dumps(result)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"MCP error: {result.get('error')}",
                    "message": f"Could not check availability for room {room_id}"
                })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"MCP connection failed: {e}",
                "message": f"Cannot check availability for room {room_id}"
            })

    async def get_rooms_via_mcp(self) -> str:
        """Get rooms via MCP server."""
        try:
            health = await self.mcp_client.health_check()
            if not health.get("status") == "healthy":
                return json.dumps({
                    "success": False,
                    "error": "MCP server not available",
                    "message": "Cannot retrieve room list"
                })
            
            result = await self.mcp_client.get_rooms_via_mcp()
            if result.get("success"):
                return json.dumps(result)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"MCP error: {result.get('error')}",
                    "message": "Could not retrieve room list"
                })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"MCP connection failed: {e}",
                "message": "Cannot retrieve room list"
            })

    async def schedule_event_via_mcp(self, title: str, start_time: str, end_time: str, 
                                   room_id: str, organizer: str, description: str = "") -> str:
        """Schedule event via MCP server."""
        try:
            health = await self.mcp_client.health_check()
            if not health.get("status") == "healthy":
                return json.dumps({
                    "success": False,
                    "error": "MCP server not available",
                    "message": f"Cannot schedule event '{title}'"
                })
            
            result = await self.mcp_client.create_event_via_mcp(
                user_id=organizer,
                calendar_id=room_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description
            )
            if result.get("success"):
                return json.dumps(result)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"MCP error: {result.get('error')}",
                    "message": f"Could not schedule event '{title}'"
                })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"MCP connection failed: {e}",
                "message": f"Cannot schedule event '{title}'"
            })

    async def schedule_event_with_organizer(self, room_id: str, title: str, 
                                         start_time: str, end_time: str, organizer: str, description: str = "") -> str:
        """Schedule an event without permission checking - just collect organizer info."""
        try:
            result = await self.schedule_event_via_mcp(
                title=title,
                start_time=start_time,
                end_time=end_time,
                room_id=room_id,
                organizer=organizer,
                description=description
            )
            return result
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error scheduling event: {str(e)}"
            })

    def fetch_user_directory(self) -> Dict[str, Any]:
        """Fetch user directory from uploaded Azure resource."""
        url = os.getenv("USER_DIRECTORY_URL")
        if not url:
            return {}
        
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to load user directory: {e}")
            return {}

    async def add_agent_tools(self) -> Optional[Any]:
        """Add tools for the agent."""
        font_file_info = None

        # Add the functions tool
        self.toolset.add(self.functions)

        # Add the code interpreter tool for data visualization
        code_interpreter = CodeInterpreterTool()
        self.toolset.add(code_interpreter)

        # Add multilingual support to the code interpreter
        try:
            font_file_info = await self.utilities.upload_file(
                self.project_client, 
                self.utilities.shared_files_path / FONTS_ZIP
            )
            code_interpreter.add_file(file_id=font_file_info.id)
        except Exception as e:
            logger.warning(f"Could not upload fonts file: {e}")

        return font_file_info

    async def initialize_agent(self) -> Tuple[bool, str]:
        """Initialize the agent. Returns (success, message)."""
        if not INSTRUCTIONS_FILE:
            return False, "Instructions file not specified"

        try:
            # Initialize project client
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=PROJECT_CONNECTION_STRING,
            )

            # Add agent tools
            font_file_info = await self.add_agent_tools()

            # Load instructions
            instructions = self.utilities.load_instructions(INSTRUCTIONS_FILE)
            if font_file_info:
                instructions = instructions.replace("{font_file_id}", font_file_info.id)

            # Create agent
            self.agent = await self.project_client.agents.create_agent(
                model=API_DEPLOYMENT_NAME,
                name=AGENT_NAME,
                instructions=instructions,
                toolset=self.toolset,
                temperature=TEMPERATURE,
            )

            # Test MCP server connectivity
            try:
                health = await self.mcp_client.health_check()
                mcp_status = "healthy" if health.get("status") == "healthy" else "unhealthy"
            except Exception:
                mcp_status = "unreachable"

            # Test user directory access
            users = self.fetch_user_directory()
            user_dir_status = f"loaded ({len(users)} entries)" if users else "empty/inaccessible"

            # Enable auto function calls
            self.project_client.agents.enable_auto_function_calls(toolset=self.toolset)

            # Create thread
            self.thread = await self.project_client.agents.create_thread()

            # Create shared communication thread
            shared_thread = await self.project_client.agents.create_thread()
            self.shared_thread_id = shared_thread.id

            # Post initialization message
            event_payload = {
                "event": "initialized",
                "message": "Calendar agent is now active and ready to schedule events",
                "updated_by": "calendar-agent"
            }
            await self.project_client.agents.create_message(
                thread_id=shared_thread.id,
                role="user",
                content=json.dumps(event_payload)
            )

            success_msg = f"Agent initialized successfully. MCP: {mcp_status}, User Directory: {user_dir_status}"
            return True, success_msg

        except Exception as e:
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def process_message(self, message: str, for_streamlit: bool = False) -> Tuple[bool, str]:
        """Process a message with the agent. Returns (success, response)."""
        if not self.agent or not self.thread:
            return False, "Agent not initialized"

        try:
            # Create message
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message,
            )

            # Choose appropriate event handler
            if for_streamlit:
                stream_handler = StreamlitEventHandler(
                    functions=self.functions,
                    project_client=self.project_client,
                    utilities=self.utilities
                )
            else:
                stream_handler = StreamEventHandler(
                    functions=self.functions,
                    project_client=self.project_client,
                    utilities=self.utilities
                )

            stream_handler.current_user_query = message

            # Create and process stream
            stream = await self.project_client.agents.create_stream(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                event_handler=stream_handler,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                max_prompt_tokens=MAX_PROMPT_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                instructions=self.agent.instructions,
            )

            async with stream as s:
                await s.until_done()

            if for_streamlit:
                return True, stream_handler.captured_response
            else:
                return True, "Response printed to console"

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        if self.project_client and self.agent and self.thread:
            try:
                # Delete files
                existing_files = await self.project_client.agents.list_files()
                for f in existing_files.data:
                    await self.project_client.agents.delete_file(f.id)
                
                # Delete thread and agent
                await self.project_client.agents.delete_thread(self.thread.id)
                await self.project_client.agents.delete_agent(self.agent.id)
                
                logger.info("Agent resources cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                # Close MCP client connections
                try:
                    if hasattr(self.mcp_client, 'cleanup'):
                        await self.mcp_client.cleanup()
                    if hasattr(self.microsoft_docs_client, 'cleanup'):
                        await self.microsoft_docs_client.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up MCP clients: {e}")
                
                # Close the project client connection
                if hasattr(self.project_client, 'close'):
                    await self.project_client.close()
                elif hasattr(self.project_client, '_client') and hasattr(self.project_client._client, 'close'):
                    await self.project_client._client.close()
                
                # Reset state
                self.agent = None
                self.thread = None
                self.project_client = None

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status for UI display."""
        status = {
            "agent_initialized": self.agent is not None,
            "thread_created": self.thread is not None,
            "agent_id": self.agent.id if self.agent else None,
            "thread_id": self.thread.id if self.thread else None,
            "shared_thread_id": self.shared_thread_id,
        }
        
        # Check MCP health
        try:
            health = await self.mcp_client.health_check()
            status["mcp_status"] = "healthy" if health.get("status") == "healthy" else "unhealthy"
        except Exception:
            status["mcp_status"] = "unreachable"
        
        # Check Microsoft Docs MCP health
        try:
            docs_health = await self.microsoft_docs_client.health_check()
            status["microsoft_docs_mcp_status"] = "healthy" if docs_health.get("status") == "healthy" else "unhealthy"
        except Exception:
            status["microsoft_docs_mcp_status"] = "unreachable"
        
        # Check user directory
        users = self.fetch_user_directory()
        status["user_directory"] = {
            "loaded": len(users) > 0,
            "count": len(users)
        }
        
        return status

    async def search_microsoft_documentation(self, query: str) -> str:
        """
        Search Microsoft's official documentation including Azure docs, Microsoft Learn, 
        and other Microsoft technical documentation.
        
        Use this function when you need to:
        - Get official Microsoft documentation about Azure services
        - Find authoritative information about Microsoft technologies
        - Get up-to-date information about Microsoft APIs, SDKs, or services
        - Answer questions about Microsoft best practices or implementation details
        
        Args:
            query (str): The search query for Microsoft documentation.
                        Examples: "Azure Container Apps", "Azure CLI commands", 
                        "ASP.NET Core authentication", "Azure Functions deployment"
        
        Returns:
            str: JSON string containing search results from Microsoft documentation
        """
        try:
            # Check if Microsoft Docs MCP server is available
            health = await self.microsoft_docs_client.health_check()
            if health.get("status") != "healthy":
                return json.dumps({
                    "success": False,
                    "error": "Microsoft Docs MCP server not available",
                    "message": f"Cannot search Microsoft documentation for: {query}",
                    "health_status": health
                })
            
            # Perform the search
            result = await self.microsoft_docs_client.search_microsoft_docs(query)
            
            if result.get("success"):
                # Format the results for better readability
                formatted_results = []
                for doc in result.get("results", []):
                    formatted_results.append({
                        "content": doc.get("content", ""),
                        "type": doc.get("type", "documentation"),
                        "source": "Microsoft Learn Docs"
                    })
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "results": formatted_results,
                    "source": "Microsoft Learn Docs MCP Server",
                    "message": f"Found {len(formatted_results)} documentation results for: {query}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Could not search Microsoft documentation for: {query}"
                })
                
        except Exception as e:
            logger.error(f"Error searching Microsoft documentation: {e}")
            return json.dumps({
                "success": False,
                "error": f"Microsoft Docs search failed: {str(e)}",
                "message": f"Could not search Microsoft documentation for: {query}"
            })
