"""
Core agent functionality for the Calendar Scheduling Agent.
This module contains the reusable agent logic that can be used by the terminal interface (main.py).
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

    async def add_agent_tools(self) -> Optional[Any]:
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
            # Parse connection string format: host;subscription_id;resource_group_name;project_name
            parts = PROJECT_CONNECTION_STRING.split(';')
            if len(parts) != 4:
                return False, f"Invalid PROJECT_CONNECTION_STRING format. Expected 4 parts, got {len(parts)}"
            
            host = parts[0]              # uksouth.api.azureml.ms
            subscription_id = parts[1]   # 6797c788-362f-45f5-a36e-6b8d83b7121c
            resource_group_name = parts[2]  # azure_for_students_agents_hub  
            project_name = parts[3]      # new_ixn_agents_resources
            
            logger.info(f"[AgentCore] Parsed connection string:")
            logger.info(f"[AgentCore]   Host: {host}")
            logger.info(f"[AgentCore]   Subscription ID: {subscription_id}")
            logger.info(f"[AgentCore]   Resource Group: {resource_group_name}")
            logger.info(f"[AgentCore]   Project: {project_name}")

            # Your project is hub-based, so we should use the from_connection_string method
            # According to the migration guide, hub-based projects use this format:
            # project_client = AIProjectClient.from_connection_string(
            #     credential=DefaultAzureCredential(),
            #     conn_str=connection_string,
            # )
            
            logger.info(f"[AgentCore] Using hub-based project with connection string")
            logger.info(f"[AgentCore] This matches your Azure AI Projects SDK version 1.0.0b10")

            # Initialize AIProjectClient using the hub-based connection string method
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
            logger.info(f"[AgentCore] Created agent with ID: {self.agent.id}")

            # Check MCP health status
            try:
                health = await self.mcp_client.health_check()
                mcp_status = "healthy" if health.get("status") == "healthy" else "unhealthy"
            except Exception:
                mcp_status = "unreachable"

            # Check user directory status  
            users = self.fetch_user_directory()
            user_dir_status = f"loaded ({len(users)} entries)" if users else "empty/inaccessible"

            # Enable auto function calls - this might be causing the toolset issue
            # For hub-based projects, we might need to handle this differently
            try:
                await self.project_client.agents.enable_auto_function_calls(toolset=self.toolset)
                logger.info(f"[AgentCore] Auto function calls enabled successfully")
            except Exception as e:
                logger.warning(f"[AgentCore] Could not enable auto function calls: {e}")
                # Continue without auto function calls for now

            # Create thread - using hub-based API structure
            # Hub-based: project_client.agents.create_thread()
            # Endpoint-based: project_client.agents.threads.create()
            self.thread = await self.project_client.agents.create_thread()
            logger.info(f"[AgentCore] Created thread with ID: {self.thread.id}")

            # Create shared thread for system events - using hub-based API
            shared_thread = await self.project_client.agents.create_thread()
            self.shared_thread_id = shared_thread.id
            logger.info(f"[AgentCore] Created shared thread with ID: {self.shared_thread_id}")

            # Send initialization event to shared thread - using hub-based API
            # Hub-based: project_client.agents.create_message()
            # Endpoint-based: project_client.agents.messages.create()
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
            logger.info(f"[AgentCore] Initialization complete. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
            return True, success_msg
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(f"[AgentCore] Initialization error: {error_msg}")
            return False, error_msg

    async def process_message(self, message: str) -> Tuple[bool, str]:
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
            # Use the already initialized project client
            if not self.project_client:
                return False, "Project client not initialized"
                
            # Enable auto function calls for this client
            try:
                await self.project_client.agents.enable_auto_function_calls(toolset=self.toolset)
            except Exception as e:
                logger.warning(f"[AgentCore] Could not enable auto function calls: {e}")
            
            # Create message using hub-based API
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=message,
            )
            logger.info(f"[AgentCore] Message created for thread ID: {self.thread.id}")

            stream_handler = StreamEventHandler(
                functions=self.functions,
                project_client=self.project_client,
                utilities=self.utilities
            )

            stream_handler.current_user_query = message
            # Create stream using hub-based API
            # Hub-based: project_client.agents.create_stream()
            # Endpoint-based: project_client.agents.runs.stream()
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
            logger.info(f"[AgentCore] Run started for thread ID: {self.thread.id}, Agent ID: {self.agent.id}")
            
            async with stream as s:
                await s.until_done()
            logger.info(f"[AgentCore] Run completed for thread ID: {self.thread.id}")
            
            # Check if run is stuck in REQUIRES_ACTION and handle it manually
            runs_paged = await self.project_client.agents.list_runs(thread_id=self.thread.id)
            if hasattr(runs_paged, 'data') and runs_paged.data:
                latest_run = runs_paged.data[0]  # Most recent run
                if getattr(latest_run, 'status', None) == 'requires_action':
                    logger.warning(f"[AgentCore] Run {latest_run.id} is stuck in REQUIRES_ACTION, handling manually")
                    await self._handle_required_action(latest_run)
            
            # Diagnostic logging for stream_handler state
            logger.warning(f"[AgentCore][DEBUG] stream_handler.captured_response: {getattr(stream_handler, 'captured_response', None)}")
            logger.warning(f"[AgentCore][DEBUG] stream_handler.current_response_text: {getattr(stream_handler, 'current_response_text', None)}")
            logger.warning(f"[AgentCore][DEBUG] stream_handler.__dict__: {stream_handler.__dict__}")

            # Fetch and log all thread messages for this thread - using hub-based API
            try:
                # Hub-based: list_messages()
                # Endpoint-based: messages.list()
                thread_messages_paged = await self.project_client.agents.list_messages(thread_id=self.thread.id)
                logger.warning(f"[AgentCore][DEBUG] Thread messages for thread {self.thread.id}:")
                # For hub-based API, messages might be in .data attribute
                if hasattr(thread_messages_paged, 'data'):
                    for msg in thread_messages_paged.data:
                        logger.warning(f"[AgentCore][DEBUG] Message: id={getattr(msg, 'id', None)}, role={getattr(msg, 'role', None)}, status={getattr(msg, 'status', None)}, content={getattr(msg, 'content', None)}")
                else:
                    # If it's an async iterator, iterate properly
                    async for msg in thread_messages_paged:
                        logger.warning(f"[AgentCore][DEBUG] Message: id={getattr(msg, 'id', None)}, role={getattr(msg, 'role', None)}, status={getattr(msg, 'status', None)}, content={getattr(msg, 'content', None)}")
            except Exception as e:
                logger.error(f"[AgentCore][DEBUG] Error fetching thread messages: {e}")

            # Optionally log the final run object if available - using hub-based API
            try:
                # Hub-based: list_runs()
                # Endpoint-based: runs.list()
                runs_paged = await self.project_client.agents.list_runs(thread_id=self.thread.id)
                logger.warning(f"[AgentCore][DEBUG] Runs for thread {self.thread.id}:")
                # For hub-based API, runs might be in .data attribute
                if hasattr(runs_paged, 'data'):
                    for run in runs_paged.data:
                        logger.warning(f"[AgentCore][DEBUG] Run: id={getattr(run, 'id', None)}, status={getattr(run, 'status', None)}, last_error={getattr(run, 'last_error', None)}")
                        # If run requires action, log the required action/tool
                        if getattr(run, 'status', None) == 'REQUIRES_ACTION':
                            required_action = getattr(run, 'required_action', None)
                            logger.warning(f"[AgentCore][DEBUG] Run requires action: {required_action}")
                            tool_calls = getattr(run, 'tool_calls', None)
                            logger.warning(f"[AgentCore][DEBUG] Run tool_calls: {tool_calls}")
                else:
                    # If it's an async iterator, iterate properly
                    async for run in runs_paged:
                        logger.warning(f"[AgentCore][DEBUG] Run: id={getattr(run, 'id', None)}, status={getattr(run, 'status', None)}, last_error={getattr(run, 'last_error', None)}")
            except Exception as e:
                logger.error(f"[AgentCore][DEBUG] Error fetching runs: {e}")

            response_text = (
                getattr(stream_handler, "captured_response", None)
                or getattr(stream_handler, "current_response_text", "")
            )
            
            # If we still don't have a response, try to get the latest assistant message from the thread
            if not response_text.strip():
                try:
                    thread_messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
                    if hasattr(thread_messages, 'data') and thread_messages.data:
                        # Look for the most recent assistant message
                        for message in thread_messages.data:
                            if getattr(message, 'role', None) == 'assistant':
                                content = getattr(message, 'content', [])
                                for content_item in content:
                                    if hasattr(content_item, 'text') and content_item.text:
                                        if hasattr(content_item.text, 'value'):
                                            response_text += content_item.text.value
                                        else:
                                            response_text += str(content_item.text)
                                if response_text.strip():  # If we found content, stop looking
                                    break
                    else:
                        # Handle async iterator
                        async for message in thread_messages:
                            if getattr(message, 'role', None) == 'assistant':
                                content = getattr(message, 'content', [])
                                for content_item in content:
                                    if hasattr(content_item, 'text') and content_item.text:
                                        if hasattr(content_item.text, 'value'):
                                            response_text += content_item.text.value
                                        else:
                                            response_text += str(content_item.text)
                                if response_text.strip():  # If we found content, stop looking
                                    break
                except Exception as e:
                    logger.warning(f"[AgentCore] Could not fetch latest message: {e}")
            
            return True, response_text
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"[AgentCore] Error processing message: {error_msg}")
            return False, error_msg
        finally:
            self._operation_active = False
            logger.info(f"[AgentCore] Operation complete. Agent ID: {self.agent.id if self.agent else None}, Thread ID: {self.thread.id if self.thread else None}")

    async def _handle_required_action(self, run):
        """Handle runs that require action (tool calls)."""
        try:
            import json
            if hasattr(run, 'required_action') and run.required_action:
                required_action = run.required_action
                if hasattr(required_action, 'submit_tool_outputs') and required_action.submit_tool_outputs:
                    tool_calls = required_action.submit_tool_outputs.tool_calls
                    logger.info(f"[AgentCore] Handling {len(tool_calls)} tool calls")
                    
                    tool_outputs = []
                    for tool_call in tool_calls:
                        if tool_call.type == "function":
                            function_name = tool_call.function.name
                            function_args = tool_call.function.arguments
                            
                            logger.info(f"[AgentCore] Executing function: {function_name}")
                            logger.info(f"[AgentCore] Function arguments: {function_args}")
                            
                            try:
                                # Parse arguments
                                args = json.loads(function_args) if function_args else {}
                                
                                # Execute the function directly by name
                                if function_name == "get_rooms_via_mcp":
                                    result = await self.get_rooms_via_mcp()
                                elif function_name == "get_events_via_mcp":
                                    result = await self.get_events_via_mcp()
                                elif function_name == "check_room_availability_via_mcp":
                                    result = await self.check_room_availability_via_mcp(
                                        args.get("room_id", ""),
                                        args.get("start_time", ""),
                                        args.get("end_time", "")
                                    )
                                elif function_name == "schedule_event_with_organizer":
                                    result = await self.schedule_event_with_organizer(
                                        args.get("room_id", ""),
                                        args.get("title", ""),
                                        args.get("start_time", ""),
                                        args.get("end_time", ""),
                                        args.get("organizer", ""),
                                        args.get("description", "")
                                    )
                                else:
                                    result = json.dumps({
                                        "success": False,
                                        "error": f"Unknown function: {function_name}"
                                    })
                                
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": str(result)
                                })
                                logger.info(f"[AgentCore] Function {function_name} executed successfully")
                            except Exception as e:
                                logger.error(f"[AgentCore] Error executing function {function_name}: {e}")
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({
                                        "success": False,
                                        "error": f"Function execution failed: {str(e)}"
                                    })
                                })
                    
                    # Submit tool outputs using the correct method
                    if tool_outputs:
                        try:
                            # Try different possible method names for hub-based API
                            submit_method = None
                            for method_name in ["submit_tool_outputs_to_run", "submit_tool_outputs", "submit_tool_outputs_stream"]:
                                if hasattr(self.project_client.agents, method_name):
                                    submit_method = getattr(self.project_client.agents, method_name)
                                    logger.info(f"[AgentCore] Using method: {method_name}")
                                    break
                            
                            if submit_method:
                                await submit_method(
                                    thread_id=self.thread.id,
                                    run_id=run.id,
                                    tool_outputs=tool_outputs
                                )
                                logger.info(f"[AgentCore] Submitted {len(tool_outputs)} tool outputs")
                                
                                # Wait for the run to complete after submitting tool outputs
                                await self._wait_for_run_completion(run.id)
                                
                            else:
                                logger.error(f"[AgentCore] No suitable method found to submit tool outputs")
                        except Exception as e:
                            logger.error(f"[AgentCore] Error submitting tool outputs: {e}")
        except Exception as e:
            logger.error(f"[AgentCore] Error in _handle_required_action: {e}")

    async def _wait_for_run_completion(self, run_id: str, max_wait: int = 30):
        """Wait for a run to complete after tool outputs are submitted."""
        import asyncio
        for attempt in range(max_wait):
            try:
                run = await self.project_client.agents.get_run(
                    thread_id=self.thread.id,
                    run_id=run_id
                )
                status = getattr(run, 'status', None)
                logger.info(f"[AgentCore] Run {run_id} status: {status}")
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    logger.info(f"[AgentCore] Run {run_id} finished with status: {status}")
                    break
                elif status == 'requires_action':
                    logger.warning(f"[AgentCore] Run {run_id} still requires action after {attempt + 1} seconds")
                    break
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[AgentCore] Error checking run status: {e}")
                break

    async def cleanup(self) -> None:
        """Cleanup agent resources. Idempotent."""
        try:
            if self.agent and self.thread:
                # Use the hub-based connection string format for cleanup
                async with AIProjectClient.from_connection_string(
                    credential=DefaultAzureCredential(),
                    conn_str=PROJECT_CONNECTION_STRING,
                ) as project_client:
                    # Hub-based cleanup APIs
                    existing_files = await project_client.agents.list_files()
                    if hasattr(existing_files, 'data'):
                        for f in existing_files.data:
                            await project_client.agents.delete_file(f.id)
                    else:
                        async for f in existing_files:
                            await project_client.agents.delete_file(f.id)
                    
                    await project_client.agents.delete_thread(self.thread.id)
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
