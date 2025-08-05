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
from azure.ai.agents.models import (
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

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Calendar Scheduler"
FONTS_ZIP = "fonts/fonts.zip"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
print("[AGENT] PROJECT_CONNECTION_STRING:", PROJECT_CONNECTION_STRING)
print("[AGENT] MODEL_DEPLOYMENT_NAME:", API_DEPLOYMENT_NAME)
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
        self.toolset = AsyncToolSet()
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        self.shared_thread_id: Optional[str] = None
        self.functions = None
        self._operation_active = False  # Prevent concurrent runs
        self._initialize_functions()

    def _cleanup_run_thread(self):
        """Reset agent and thread state after operation or error."""
        self.agent = None
        self.thread = None
        self.shared_thread_id = None
        self._operation_active = False
        
    def _initialize_functions(self):
        """Initialize the function tools."""
        self.functions = AsyncFunctionTool([
            self.get_events_via_mcp,
            self.check_room_availability_via_mcp,
            self.get_rooms_via_mcp,
            self.schedule_event_with_organizer,
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

    async def add_agent_tools(self, project_client) -> Optional[Any]:
        """Add tools for the agent."""
        font_file_info = None

        # Add the functions tool
        self.toolset.add(self.functions)

        # Add the code interpreter tool for data visualization
        code_interpreter = CodeInterpreterTool()
        self.toolset.add(code_interpreter)

        # Add multilingual support to the code interpreter
        # Multilingual font upload temporarily disabled for debugging
        # try:
        #     font_file_info = await self.utilities.upload_file(
        #         project_client, 
        #         self.utilities.shared_files_path / FONTS_ZIP
        #     )
        #     code_interpreter.add_file(file_id=font_file_info.id)
        # except Exception as e:
        #     logger.warning(f"Could not upload fonts file: {e}")
        logger.info("Font file upload skipped for debugging.")

        return font_file_info

    async def initialize_agent(self) -> Tuple[bool, str]:
        logger.info("[AgentCore] Initializing agent...")
        """Initialize the agent. Returns (success, message)."""
        if not INSTRUCTIONS_FILE:
            return False, "Instructions file not specified"

        # Idempotent: cleanup any previous state
        self._cleanup_run_thread()

        try:
            parts = PROJECT_CONNECTION_STRING.split(';')
            if len(parts) != 4:
                return False, f"Invalid PROJECT_CONNECTION_STRING format. Expected 4 parts, got {len(parts)}"

            endpoint = f"https://{parts[0]}/agents/v1.0/subscriptions/{parts[1]}/resourceGroups/{parts[2]}/providers/Microsoft.MachineLearningServices/workspaces/{parts[3]}"
            logger.info(f"[AgentCore] Constructed endpoint: {endpoint}")
            logger.info(f"[AgentCore] Subscription: {parts[1]}, Resource Group: {parts[2]}, Project: {parts[3]}")

            async with AIProjectClient(
                endpoint=endpoint,
                subscription_id=parts[1],
                resource_group_name=parts[2], 
                project_name=parts[3],
                credential=DefaultAzureCredential(),
            ) as project_client:
                font_file_info = await self.add_agent_tools(project_client)
                instructions = self.utilities.load_instructions(INSTRUCTIONS_FILE)
                if font_file_info:
                    instructions = instructions.replace("{font_file_id}", font_file_info.id)
                self.agent = await project_client.agents.create_agent(
                    model=API_DEPLOYMENT_NAME,
                    name=AGENT_NAME,
                    instructions=instructions,
                    toolset=self.toolset,
                    temperature=TEMPERATURE,
                )
                logger.info(f"[AgentCore] Created agent with ID: {self.agent.id}")
                try:
                    health = await self.mcp_client.health_check()
                    mcp_status = "healthy" if health.get("status") == "healthy" else "unhealthy"
                except Exception:
                    mcp_status = "unreachable"
                users = self.fetch_user_directory()
                user_dir_status = f"loaded ({len(users)} entries)" if users else "empty/inaccessible"
                project_client.agents.enable_auto_function_calls(tools=self.toolset)
                self.thread = await project_client.agents.threads.create()
                logger.info(f"[AgentCore] Created thread with ID: {self.thread.id}")
                shared_thread = await project_client.agents.threads.create()
                self.shared_thread_id = shared_thread.id
                logger.info(f"[AgentCore] Created shared thread with ID: {self.shared_thread_id}")
                event_payload = {
                    "event": "initialized",
                    "message": "Calendar agent is now active and ready to schedule events",
                    "updated_by": "calendar-agent"
                }
                await project_client.agents.messages.create(
                    thread_id=shared_thread.id,
                    role="user",
                    content=json.dumps(event_payload)
                )
                success_msg = f"Agent initialized successfully. MCP: {mcp_status}, User Directory: {user_dir_status}"
                logger.info(f"[AgentCore] Initialization complete. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
                return True, success_msg
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(f"[AgentCore] Initialization error: {error_msg}")
            return False, error_msg

    async def process_message(self, message: str, for_streamlit: bool = False) -> Tuple[bool, str]:
        """Process a message with the agent. Returns (success, response)."""
        if not self.agent or not self.thread:
            logger.warning("[AgentCore] Agent or thread not initialized.")
            return False, "Agent not initialized"
        if self._operation_active:
            logger.warning("[AgentCore] Agent is busy processing another request.")
            return False, "Agent is busy processing another request. Please wait."
        self._operation_active = True
        logger.info(f"[AgentCore] Processing message. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
        try:
            parts = PROJECT_CONNECTION_STRING.split(';')
            endpoint = f"https://{parts[0]}/agents/v1.0/subscriptions/{parts[1]}/resourceGroups/{parts[2]}/providers/Microsoft.MachineLearningServices/workspaces/{parts[3]}"
            async with AIProjectClient(
                endpoint=endpoint,
                subscription_id=parts[1],
                resource_group_name=parts[2], 
                project_name=parts[3],
                credential=DefaultAzureCredential(),
            ) as project_client:
                # Enable auto function calls for this scoped client
                await project_client.agents.enable_auto_function_calls(toolset=self.toolset)
                
                await project_client.agents.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=message,
                )
                logger.info(f"[AgentCore] Message created for thread ID: {self.thread.id}")
                if for_streamlit:
                    stream_handler = StreamlitEventHandler(
                        functions=self.functions,
                        project_client=project_client,
                        utilities=self.utilities
                    )
                else:
                    stream_handler = StreamEventHandler(
                        functions=self.functions,
                        project_client=project_client,
                        utilities=self.utilities
                    )
                stream_handler.current_user_query = message
                stream = await project_client.agents.runs.stream(
                    thread_id=self.thread.id,
                    agent_id=self.agent.id,
                    event_handler=stream_handler,
                    max_completion_tokens=MAX_COMPLETION_TOKENS,
                    max_prompt_tokens=MAX_PROMPT_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    instructions=self.agent.instructions,
                )
                logger.info(f"[AgentCore] Run started for thread ID: {self.thread.id}, Agent ID: {self.agent.id}")
                async with stream as s:
                    await s.until_done()
                logger.info(f"[AgentCore] Run completed for thread ID: {self.thread.id}")
                # Diagnostic logging for stream_handler state
                logger.warning(f"[AgentCore][DEBUG] stream_handler.captured_response: {getattr(stream_handler, 'captured_response', None)}")
                logger.warning(f"[AgentCore][DEBUG] stream_handler.current_response_text: {getattr(stream_handler, 'current_response_text', None)}")
                logger.warning(f"[AgentCore][DEBUG] stream_handler.__dict__: {stream_handler.__dict__}")

                # Fetch and log all thread messages for this thread
                try:
                    thread_messages_paged = project_client.agents.messages.list(thread_id=self.thread.id)
                    logger.warning(f"[AgentCore][DEBUG] Thread messages for thread {self.thread.id}:")
                    async for msg in thread_messages_paged:
                        logger.warning(f"[AgentCore][DEBUG] Message: id={getattr(msg, 'id', None)}, role={getattr(msg, 'role', None)}, status={getattr(msg, 'status', None)}, content={getattr(msg, 'content', None)}")
                except Exception as e:
                    logger.error(f"[AgentCore][DEBUG] Error fetching thread messages: {e}")

                # Optionally log the final run object if available
                try:
                    runs_paged = project_client.agents.runs.list(thread_id=self.thread.id)
                    logger.warning(f"[AgentCore][DEBUG] Runs for thread {self.thread.id}:")
                    async for run in runs_paged:
                        logger.warning(f"[AgentCore][DEBUG] Run: id={getattr(run, 'id', None)}, status={getattr(run, 'status', None)}, last_error={getattr(run, 'last_error', None)}")
                        # If run requires action, log the required action/tool
                        if getattr(run, 'status', None) == 'REQUIRES_ACTION':
                            required_action = getattr(run, 'required_action', None)
                            logger.warning(f"[AgentCore][DEBUG] Run requires action: {required_action}")
                            tool_calls = getattr(run, 'tool_calls', None)
                            logger.warning(f"[AgentCore][DEBUG] Run tool_calls: {tool_calls}")
                            # Print full run object for inspection
                            logger.warning(f"[AgentCore][DEBUG] Full run object (vars): {vars(run)}")
                            logger.warning(f"[AgentCore][DEBUG] Full run object (repr): {repr(run)}")
                            # Print all available methods and attributes for run
                            logger.warning(f"[AgentCore][DEBUG] Run dir: {dir(run)}")
                except Exception as e:
                    logger.error(f"[AgentCore][DEBUG] Error fetching runs: {e}")

                if for_streamlit:
                    return True, getattr(stream_handler, 'captured_response', None)
                else:
                    response_text = (
                        getattr(stream_handler, "captured_response", None)
                        or getattr(stream_handler, "current_response_text", "")
                    )
                    return True, response_text
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"[AgentCore] Error processing message: {error_msg}")
            return False, error_msg
        finally:
            self._operation_active = False
            logger.info(f"[AgentCore] Operation complete. Agent ID: {self.agent.id if self.agent else None}, Thread ID: {self.thread.id if self.thread else None}")

    async def cleanup(self) -> None:
        """Cleanup agent resources. Idempotent."""
        try:
            if self.agent and self.thread:
                parts = PROJECT_CONNECTION_STRING.split(';')
                # Extract components from connection string
                endpoint = f"https://{parts[0]}"
                subscription_id = parts[1]
                resource_group_name = parts[2]
                project_name = parts[3]
                
                async with AIProjectClient(
                    endpoint=endpoint,
                    credential=DefaultAzureCredential(),
                    subscription_id=subscription_id,
                    resource_group_name=resource_group_name,
                    project_name=project_name,
                ) as project_client:
                    existing_files = await project_client.agents.files.list()
                    for f in existing_files.data:
                        await project_client.agents.files.delete(f.id)
                    await project_client.agents.threads.delete(self.thread.id)
                    await project_client.agents.delete_agent(self.agent.id)
                    logger.info("Agent resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            try:
                if hasattr(self.mcp_client, 'cleanup'):
                    await self.mcp_client.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up MCP clients: {e}")
            self._cleanup_run_thread()

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
        
        # Check user directory
        users = self.fetch_user_directory()
        status["user_directory"] = {
            "loaded": len(users) > 0,
            "count": len(users)
        }
        
        return status
