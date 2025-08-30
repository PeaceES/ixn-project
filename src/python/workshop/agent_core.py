"""
Core agent functionality for the Calendar Scheduling Agent.
This module contains the reusable agent logic that can be used by the terminal interface (main.py).
"""

import asyncio
import logging
import os
import json
import httpx
from typing import Optional, Tuple, Dict, Any, List
from dotenv import load_dotenv

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import MessageRole
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
# Removed verbose debug prints for cleaner output
# Only essential info will be logged
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = "../shared/instructions/general_instructions.txt"


class CalendarAgentCore:
    """Core calendar agent functionality."""
    
    def __init__(self, enable_tools: bool = True, enable_code_interpreter: bool = False):
        self.agent: Optional[Agent] = None
        self.thread: Optional[AgentThread] = None
        self.toolset = AsyncToolSet()
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        self.shared_thread_id: Optional[str] = None
        self.functions = None
        self._operation_active = False  # Prevent concurrent runs
        self._tools_initialized = False  # Track if tools are already added
        # Flag to enable or disable tools (safe-mode testing)
        self._enable_tools = enable_tools
        # Flag to separately enable the CodeInterpreter tool (for bisecting)
        self._enable_code_interpreter = enable_code_interpreter
        
        # Check for user context from environment (passed by web server)
        self.default_user_context = None
        if os.getenv('AGENT_USER_ID'):
            self.default_user_context = {
                'id': os.getenv('AGENT_USER_ID'),
                'name': os.getenv('AGENT_USER_NAME', ''),
                'email': os.getenv('AGENT_USER_EMAIL', '')
            }
            logger.info(f"[AgentCore] Initialized with user context: {self.default_user_context}")
        
        # Initialize function tools only when tools are enabled (safe-mode)
        if self._enable_tools:
            self._initialize_functions()
        else:
            logger.info("[AgentCore] Tools are disabled for this instance (safe-mode). Tools will not be initialized.")

    def __del__(self):
        """Destructor to ensure HTTP sessions are closed."""
        try:
            import asyncio
            if hasattr(self, 'mcp_client') and self.mcp_client:
                # Try to close the MCP client if we're in an event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule cleanup for later if loop is running
                        loop.create_task(self.mcp_client.close())
                    else:
                        # Run cleanup synchronously if no loop is running
                        loop.run_until_complete(self.mcp_client.close())
                except RuntimeError:
                    # No event loop available, can't clean up async resources
                    pass
        except Exception:
            # Ignore cleanup errors in destructor
            pass

    def _cleanup_run_thread(self):
        """Reset agent and thread state after operation or error."""
        self.agent = None
        self.thread = None
        self.shared_thread_id = None
        self._operation_active = False
        # Don't reset _tools_initialized as tools can be reused
        # Note: MCP client cleanup should be done in async cleanup() method
        
    def _initialize_functions(self):
        """Initialize the function tools.

        Controlled by the ENABLED_FUNCTIONS environment variable. Format:
        - "ALL" (default) to enable all functions
        - comma-separated function names to enable a subset, e.g. "get_rooms_via_mcp,check_room_availability_via_mcp"
        """
        if not self._tools_initialized:
            # Load environment configuration
            import os
            from dotenv import load_dotenv
            env_file_path = os.path.join(os.getcwd(), '.env')
            if os.path.exists(env_file_path):
                load_dotenv(override=True)  # Force reload with override
            else:
                logger.warning(f"[AgentCore] .env file not found at expected location")
            
            enabled_env = os.getenv("ENABLED_FUNCTIONS", "ALL")
            enabled_names = [s.strip() for s in enabled_env.split(',')] if enabled_env else []

            # Map of available function names to bound callables
            available_funcs = {
                "get_events_via_mcp": self.get_events_via_mcp,
                "check_room_availability_via_mcp": self.check_room_availability_via_mcp,
                "get_rooms_via_mcp": self.get_rooms_via_mcp,
                "schedule_event_with_organizer": self.schedule_event_with_organizer,
                # Provide both legacy and new names for the org loader so tests and env values keep working
                # "fetch_user_directory": self.fetch_org_structure,
                # "fetch_org_structure": self.fetch_org_structure,
                # Use the async wrapper here so the AsyncFunctionTool can await the callable
                "fetch_user_directory": self._async_fetch_org_structure,
                "fetch_org_structure": self._async_fetch_org_structure,
                "get_user_groups": self.get_user_groups,
                "get_user_booking_entity": self.get_user_booking_entity,
                "schedule_event_with_permissions": self.schedule_event_with_permissions,
                "get_user_details": self.get_user_details,
            }
            
            selected = []
            selected_names = []
            # If user requested ALL, select all available functions
            if any(n.upper() == "ALL" for n in enabled_names):
                selected = list(available_funcs.values())
                selected_names = list(available_funcs.keys())
            else:
                for name in enabled_names:
                    if not name:
                        continue
                    if name in available_funcs:
                        selected.append(available_funcs[name])
                        selected_names.append(name)
                    else:
                        logger.warning(f"[AgentCore] ENABLED_FUNCTIONS includes unknown function: {name}")

            if not selected:
                # If nothing was explicitly selected, default to ALL for backwards compatibility
                selected = list(available_funcs.values())
                selected_names = list(available_funcs.keys())

            # Initialize the AsyncFunctionTool with the selected callables
            self.functions = AsyncFunctionTool(selected)
            self._tools_initialized = True
            # Simplified logging - only show count of functions
            logger.info(f"[AgentCore] Initialized with {len(selected_names)} functions")
    
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
            # Try to resolve email if organizer is an ID or name
            org_data = self._load_org_structure()
            organizer_email = organizer  # Default to what was passed in
            
            # Try to find the user's email
            for user in org_data.get('users', []):
                # Check if organizer matches ID, email, or name
                try:
                    if user.get('id') == int(organizer):
                        organizer_email = user.get('email', organizer)
                        break
                except ValueError:
                    pass
                if user.get('email', '').lower() == organizer.lower() or user.get('name', '').lower() == organizer.lower():
                    organizer_email = user.get('email', organizer)
                    break
            
            result = await self.schedule_event_via_mcp(
                title=title,
                start_time=start_time,
                end_time=end_time,
                room_id=room_id,
                organizer=organizer_email,
                description=description
            )

            # If event was successfully created, post to shared thread
            result_data = json.loads(result) if isinstance(result, str) else result
            if result_data.get("success"):
                event_obj = result_data.get("event", {})
                attendee_email = None
                attendees = event_obj.get("attendees")
                if isinstance(attendees, list) and attendees:
                    attendee_email = attendees[0]
                await self._post_event_to_shared_thread(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    room_id=room_id,
                    organizer=organizer_email,
                    attendee_email=attendee_email,
                    description=description
                )
            
            return result
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error scheduling event: {str(e)}"
            })

    async def schedule_event_with_permissions(self, user_id: str, entity_type: str, entity_name: str, 
                                            room_id: str, title: str, start_time: str, end_time: str, 
                                            description: str = "") -> str:
        """Schedule an event with proper permission checking based on org structure."""
        import json
        try:
            import logging
            logger = logging.getLogger(__name__)
            # Get user's booking entities
            entities_result = await self.get_user_booking_entity(user_id)
            entities_data = json.loads(entities_result)
            # Debug logging removed - permissions check happening silently

            if not entities_data.get("success"):
                return json.dumps({
                    "success": False,
                    "error": "Permission check failed",
                    "message": entities_data.get("error", "Could not verify user permissions")
                })

            # Validate entity exists in org structure
            org_data = self._load_org_structure()
            entity_exists = False
            entity_id = None
            if entity_type == 'department':
                for d in org_data.get('departments', []):
                    if d['name'].lower() == entity_name.lower():
                        entity_exists = True
                        entity_id = d['id']
                        break
            elif entity_type == 'course':
                for c in org_data.get('courses', []):
                    if c['name'].lower() == entity_name.lower():
                        entity_exists = True
                        entity_id = c['id']
                        break
            elif entity_type == 'society':
                for s in org_data.get('societies', []):
                    if s['name'].lower() == entity_name.lower():
                        entity_exists = True
                        entity_id = s['id']
                        break

            if not entity_exists:
                logger.warning(f"[AgentCore] Entity not found: {entity_type} '{entity_name}'")
                return json.dumps({
                    "success": False,
                    "error": "Entity not found",
                    "message": f"{entity_type.title()} '{entity_name}' does not exist"
                })

            # Check if the requested entity is in user's allowed entities (by id)
            allowed_entities = entities_data.get("entities", [])
            can_book = False
            for entity in allowed_entities:
                if entity['type'] == entity_type and entity.get('id') == entity_id:
                    can_book = True
                    break

            if not can_book:
                logger.warning(f"[AgentCore] Permission denied for user {user_id} to book {entity_type} '{entity_name}' (id: {entity_id})")
                return json.dumps({
                    "success": False,
                    "error": "Permission denied",
                    "message": f"User cannot book for {entity_type}: {entity_name}",
                    "allowed_entities": allowed_entities
                })

            # If permissions are good, schedule the event
            # Get user's email from org structure
            org_data = self._load_org_structure()
            user_email = user_id  # Default to what was passed in
            user_name = user_id  # Default name
            
            # Try to find the user's email and name
            for user in org_data.get('users', []):
                # Check if user_id matches ID, email, or name
                try:
                    if user.get('id') == int(user_id):
                        user_email = user.get('email', user_id)
                        user_name = user.get('name', user_id)
                        break
                except ValueError:
                    pass
                if user.get('email', '').lower() == user_id.lower() or user.get('name', '').lower() == user_id.lower():
                    user_email = user.get('email', user_id)
                    user_name = user.get('name', user_id)
                    break
            
            organizer_display = f"{user_name} ({entity_type}: {entity_name})"
            
            # Include entity info in description so MCP server can extract it for attendees
            enhanced_description = description
            if enhanced_description:
                enhanced_description += f" - Organized by {user_name} for {entity_name}"
            else:
                enhanced_description = f"Organized by {user_name} for {entity_name}"
            
            # Pass the actual user's email as organizer to MCP server
            # The MCP server will extract entity from description and set it as attendee
            result = await self.schedule_event_via_mcp(
                title=title,
                start_time=start_time,
                end_time=end_time,
                room_id=room_id,
                organizer=user_email,  # Pass actual user's email as organizer
                description=enhanced_description
            )

            # If event was successfully created, post to shared thread
            result_data = json.loads(result) if isinstance(result, str) else result
            if result_data.get("success"):
                await self._post_event_to_shared_thread(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    room_id=room_id,
                    organizer=organizer_display,  # Use the display version for the shared thread
                    description=description
                )

            return result

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[AgentCore] Error scheduling event with permissions: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error scheduling event with permissions: {str(e)}"
            })

    async def _post_event_to_shared_thread(self, title: str, start_time: str, end_time: str, 
                                         room_id: str, organizer: str, attendee_email: str = None, description: str = "") -> None:
        """Post a newly created event to the shared thread for visibility."""
        try:
            if not self.shared_thread_id or not self.project_client:
                logger.warning("[AgentCore] Cannot post to shared thread - thread ID or client not available")
                return

            # Use same extraction logic as MCP server
            def extract_entity_from_description(description: str):
                import re
                for_pattern = r"organized by .+? for (?:the )?(.+?)(?:\.|,|$)"
                match = re.search(for_pattern, description, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                patterns = [
                    r"organized by the (.+?)(?:\.|,|$)",
                    r"organized by (.+?)(?:\.|,|$)",
                ]
                for pattern in patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                return None

            def find_entity_email(entity_name: str):
                if not entity_name:
                    return None
                import os, json
                org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
                try:
                    with open(org_path, 'r') as f:
                        org_data = json.load(f)
                except Exception:
                    return None
                normalized_name = entity_name.lower().strip()
                for dept in org_data.get('departments', []):
                    if dept.get('name', '').lower() == normalized_name:
                        return dept.get('email')
                for society in org_data.get('societies', []):
                    if society.get('name', '').lower() == normalized_name:
                        return society.get('email')
                for course in org_data.get('courses', []):
                    if course.get('name', '').lower() == normalized_name:
                        return course.get('email')
                return None

            # If attendee_email is not provided, extract from description
            if attendee_email is None:
                entity_name = extract_entity_from_description(description or "")
                attendee_email = find_entity_email(entity_name) if entity_name else None

            event_payload = {
                "event": "event_created",
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "room_id": room_id,
                "organizer": organizer,
                "attendee_email": attendee_email,
                "description": description,
                "created_by": "calendar-agent",
                "timestamp": start_time  # Using event start time as the timestamp
            }

            await self.project_client.agents.create_message(
                thread_id=self.shared_thread_id,
                role="user",
                content=json.dumps(event_payload)
            )
            logger.info(f"[AgentCore] Posted event '{title}' to shared thread {self.shared_thread_id}")

        except Exception as e:
            logger.error(f"[AgentCore] Failed to post event to shared thread: {e}")

    def fetch_org_structure(self) -> Dict[str, Any]:
        """Load organization structure from local org_structure.json and return users keyed by email.

        This is intentionally local-only (no network calls). It reads
        src/shared/database/data-generator/org_structure.json and returns a
        dict where keys are lowercase emails and values are the user objects.
        """
        org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
        org_abspath = os.path.abspath(org_path)
        try:
            with open(org_abspath, 'r') as f:
                org_data = json.load(f)

            users = {}
            for user in org_data.get('users', []):
                email = user.get('email', '').lower()
                if email:
                    users[email] = user

            logger.info(f"[AgentCore] Loaded org_structure.json from {org_abspath} ({len(users)} users)")
            return users
        except Exception:
            # Log full stack trace to help debugging file access / JSON errors
            logger.exception(f"[AgentCore] Failed to load org_structure.json at {org_abspath}")
            return {}

    # Async wrapper for function tool consumption
    async def _async_fetch_org_structure(self) -> str:
        """Fetch the organization directory with all users, staff, and their contact information.
        
        Use this function to get user information, find users by name or email, 
        retrieve the complete organization directory/user list, or when asked to 
        "fetch users", "get users", "show users", or "list users".
        
        Returns a JSON string with success and a list of user objects containing
        names, emails, departments, roles, and other user details.
        """
        import json
        try:
            users = self.fetch_org_structure()
            user_list = list(users.values())
            
            # Create a more concise, agent-friendly response
            user_summary = []
            for user in user_list:
                user_summary.append({
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "role": user.get("role_scope"),
                    "department_id": user.get("department_id")
                })
            
            response = {
                "success": True,
                "message": f"Found {len(user_list)} users in the organization directory",
                "total_users": len(user_list),
                "users": user_summary[:10]  # Limit to first 10 for readability
            }
            
            if len(user_list) > 10:
                response["note"] = f"Showing first 10 of {len(user_list)} users. Full list available on request."
            
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.exception("[AgentCore] Failed to run async fetch_org_structure")
            return json.dumps({
                "success": False, 
                "error": str(e),
                "message": "Failed to load organization directory"
            })

    # Backwards compatible wrapper: keep the old function name working
    def fetch_user_directory(self) -> Dict[str, Any]:
        """Backward-compatible wrapper that returns the same data as fetch_org_structure."""
        return self.fetch_org_structure()

    def get_user_details(self, user_id: str) -> str:
        """Get detailed information about a user from org structure."""
        import json
        try:
            org_data = self._load_org_structure()
            users = org_data.get('users', [])
            
            # Try to find user by various methods
            user = None
            try:
                # Try by ID
                user_id_int = int(user_id)
                user = next((u for u in users if u.get('id') == user_id_int), None)
            except ValueError:
                # Try by email or name
                user = next((u for u in users if 
                           u.get('email', '').lower() == user_id.lower() or
                           u.get('name', '').lower() == user_id.lower()), None)
            
            if not user:
                return json.dumps({
                    "success": False,
                    "error": f"User '{user_id}' not found in organization"
                })
            
            # Get department, courses, and societies this user can book for
            booking_entities = self._get_user_booking_entities(user, org_data)
            
            return json.dumps({
                "success": True,
                "user": user,
                "booking_entities": booking_entities
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error fetching user details: {str(e)}"
            })

    async def get_user_groups(self, user_id: str) -> str:
        """Get groups/entities that a user can book for."""
        import json
        try:
            org_data = self._load_org_structure()
            users = org_data.get('users', [])
            
            # Find user
            user = None
            try:
                user_id_int = int(user_id)
                user = next((u for u in users if u.get('id') == user_id_int), None)
            except ValueError:
                user = next((u for u in users if 
                           u.get('email', '').lower() == user_id.lower() or
                           u.get('name', '').lower() == user_id.lower()), None)
            
            if not user:
                return json.dumps({
                    "success": False,
                    "error": f"User '{user_id}' not found"
                })
            
            booking_entities = self._get_user_booking_entities(user, org_data)
            
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "user_name": user.get('name'),
                "role": user.get('role_scope'),
                "entities": booking_entities
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error getting user groups: {str(e)}"
            })

    async def get_user_booking_entity(self, user_id: str) -> str:
        """Get all entities (departments, courses, societies) a user can book for."""
        import json
        try:
            org_data = self._load_org_structure()
            users = org_data.get('users', [])
            
            # Find user
            user = None
            try:
                user_id_int = int(user_id)
                user = next((u for u in users if u.get('id') == user_id_int), None)
            except ValueError:
                user = next((u for u in users if 
                           u.get('email', '').lower() == user_id.lower() or
                           u.get('name', '').lower() == user_id.lower()), None)
            
            if not user:
                return json.dumps({
                    "success": False,
                    "error": f"User '{user_id}' not found"
                })
            
            # Get user's booking entities using the extracted logic
            entities = []
            
            user_role = user.get('role_scope', '')
            user_dept_id = user.get('department_id')
            user_scope_id = user.get('scope_id')
            
            departments = org_data.get('departments', [])
            courses = org_data.get('courses', [])
            societies = org_data.get('societies', [])
            
            if user_role in ['department', 'staff']:
                # Department staff can book for their department
                dept = next((d for d in departments if d.get('id') == user_dept_id), None)
                if dept:
                    entities.append({
                        'type': 'department',
                        'id': dept['id'],
                        'name': dept['name'],
                        'email': dept['email']
                    })
                
                # And for any course in their department
                for course in courses:
                    if course.get('department_id') == user_dept_id:
                        entities.append({
                            'type': 'course',
                            'id': course['id'],
                            'name': course['name'],
                            'email': course['email']
                        })
                
                # And for any society in their department
                for society in societies:
                    if society.get('department_id') == user_dept_id:
                        entities.append({
                            'type': 'society',
                            'id': society['id'],
                            'name': society['name'],
                            'email': society['email']
                        })
            
            elif user_role == 'society_officer':
                # Society officers can only book for their own society
                society = next((s for s in societies if s.get('id') == user_scope_id), None)
                if society:
                    entities.append({
                        'type': 'society',
                        'id': society['id'],
                        'name': society['name'],
                        'email': society['email']
                    })
            
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "user_name": user.get('name'),
                "role": user.get('role_scope'),
                "entities": entities
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error getting user booking entities: {str(e)}"
            })

    def _load_org_structure(self) -> Dict:
        """Load organization structure from JSON file."""
        import os, json
        org_path = os.path.join(os.path.dirname(__file__), '../../shared/database/data-generator/org_structure.json')
        try:
            with open(org_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load org_structure.json: {e}")
            return {}

    def _get_user_booking_entities(self, user: Dict, org_data: Dict) -> List[Dict]:
        """Get all entities (departments, courses, societies) a user can book for."""
        entities = []
        
        user_role = user.get('role_scope', '')
        user_dept_id = user.get('department_id')
        user_scope_id = user.get('scope_id')
        
        departments = org_data.get('departments', [])
        courses = org_data.get('courses', [])
        societies = org_data.get('societies', [])
        
        if user_role in ['department', 'staff']:
            # Department staff can book for their department
            dept = next((d for d in departments if d.get('id') == user_dept_id), None)
            if dept:
                entities.append({
                    'type': 'department',
                    'id': dept['id'],
                    'name': dept['name'],
                    'email': dept['email']
                })
            
            # And for any course in their department
            for course in courses:
                if course.get('department_id') == user_dept_id:
                    entities.append({
                        'type': 'course',
                        'id': course['id'],
                        'name': course['name'],
                        'email': course['email']
                    })
            
            # And for any society in their department
            for society in societies:
                if society.get('department_id') == user_dept_id:
                    entities.append({
                        'type': 'society',
                        'id': society['id'],
                        'name': society['name'],
                        'email': society['email']
                    })
        
        elif user_role == 'society_officer':
            # Society officers can only book for their own society
            society = next((s for s in societies if s.get('id') == user_scope_id), None)
            if society:
                entities.append({
                    'type': 'society',
                    'id': society['id'],
                    'name': society['name'],
                    'email': society['email']
                })
        
        return entities

    async def add_agent_tools(self) -> Optional[Any]:
        """Add tools for the agent."""
        font_file_info = None

        if not self._enable_tools:
            logger.info("[AgentCore] add_agent_tools skipped because tools are disabled for this instance")
            return None

        # Only add functions tool if not already added
        if self.functions and not any(tool == self.functions for tool in self.toolset._tools):
            self.toolset.add(self.functions)
            logger.info("[AgentCore] Added functions tool to toolset")
        else:
            logger.info("[AgentCore] Functions tool already in toolset, skipping")

        # Add the code interpreter tool for data visualization
        if self._enable_code_interpreter:
            code_interpreter = CodeInterpreterTool()
            # Check if code interpreter is already added
            if not any(isinstance(tool, CodeInterpreterTool) for tool in self.toolset._tools):
                self.toolset.add(code_interpreter)
                logger.info("[AgentCore] Added code interpreter tool to toolset")
            else:
                logger.info("[AgentCore] Code interpreter tool already in toolset, skipping")
        else:
            logger.info("[AgentCore] Code interpreter tool not enabled for this run (skipping)")

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
            
            # Initialize project client

            # Initialize AIProjectClient using the hub-based connection string method
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=PROJECT_CONNECTION_STRING,
            )

            # Add agent tools
            # Add agent tools
            font_file_info = await self.add_agent_tools()

            # Load instructions
            instructions = self.utilities.load_instructions(INSTRUCTIONS_FILE)
            if font_file_info:
                instructions = instructions.replace("{font_file_id}", font_file_info.id)

            # Create agent
            # Create agent with hub-based connection string format
            try:
                self.agent = await self.project_client.agents.create_agent(
                    model=API_DEPLOYMENT_NAME,
                    name=AGENT_NAME,
                    instructions=instructions,
                    temperature=TEMPERATURE,
                )
                # Agent created successfully - log will be consolidated at the end
            except Exception as e:
                logger.error(f"[AgentCore] Failed to create agent with model '{API_DEPLOYMENT_NAME}': {e}")
                # Try to get available models
                try:
                    # This might help us see what models are available
                    logger.error(f"[AgentCore] Check that model '{API_DEPLOYMENT_NAME}' is deployed in your AI Foundry project")
                    logger.error(f"[AgentCore] Project connection: {PROJECT_CONNECTION_STRING}")
                except Exception:
                    pass
                raise e

            # Check MCP health status
            try:
                health = await self.mcp_client.health_check()
                mcp_status = "healthy" if health.get("status") == "healthy" else "unhealthy"
            except Exception:
                mcp_status = "unreachable"

            # Check org structure status
            org_data = self._load_org_structure()
            users = org_data.get('users', []) if isinstance(org_data, dict) else []
            user_dir_status = f"loaded ({len(users)} entries)" if users else "empty/inaccessible"

            # Enable auto function calls - this might be causing the toolset issue
            # For hub-based projects, we might need to handle this differently
            try:
                # Only enable auto function calls if tools are properly initialized
                if self._enable_tools and self._tools_initialized and len(self.toolset._tools) > 0:
                    await self.project_client.agents.enable_auto_function_calls(toolset=self.toolset)
                    # Auto function calls enabled
            except Exception as e:
                # Silently handle auto function call setup errors
                # Try alternative approach - create agent with toolset included if possible
                try:
                    if self._enable_tools and self._tools_initialized:
                        # Recreate agent with toolset
                        self.agent = await self.project_client.agents.create_agent(
                            model=API_DEPLOYMENT_NAME,
                            name=AGENT_NAME,
                            instructions=instructions,
                            toolset=self.toolset,
                            temperature=TEMPERATURE,
                        )
                        # Agent recreated with toolset integrated
                except Exception as e2:
                    logger.warning(f"[AgentCore] Could not recreate agent with toolset: {e2}")
                    # Continue without tools for basic functionality

            # Create thread - using hub-based API structure
            # Hub-based: project_client.agents.create_thread()
            # Endpoint-based: project_client.agents.threads.create()
            self.thread = await self.project_client.agents.create_thread()
            # Thread created

            # Create shared thread for system events - using hub-based API
            shared_thread = await self.project_client.agents.create_thread()
            self.shared_thread_id = shared_thread.id
            # Shared thread created

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

            # Consolidated initialization logging with essential info only
            logger.info(f"[AgentCore] Agent initialized successfully")
            logger.info(f"  - Model: {API_DEPLOYMENT_NAME}")
            logger.info(f"  - Agent ID: {self.agent.id}")
            logger.info(f"  - Thread ID: {self.thread.id}")
            logger.info(f"  - Shared Thread ID: {self.shared_thread_id}")
            logger.info(f"  - MCP Status: {mcp_status}")
            
            success_msg = f"Agent ready (Model: {API_DEPLOYMENT_NAME})"
            return True, success_msg
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(f"[AgentCore] Initialization error: {error_msg}")
            return False, error_msg

    async def process_message(self, user_message: str) -> Tuple[bool, str]:
        """Process a message with the agent. Returns (success, response)."""
        if not self.agent or not self.thread:
            logger.warning("[AgentCore] Agent or thread not initialized.")
            return False, "Agent not initialized"
        if self._operation_active:
            logger.warning("[AgentCore] Agent is busy processing another request.")
            return False, "Agent is busy processing another request. Please wait."
        self._operation_active = True
        # Process message silently unless there's an error
        try:
            # Use the already initialized project client
            if not self.project_client:
                return False, "Project client not initialized"
                
            # Ensure toolset is properly configured before each run
            try:
                if self._enable_tools and self._tools_initialized and len(self.toolset._tools) > 0:
                    await self.project_client.agents.enable_auto_function_calls(toolset=self.toolset)
            except Exception as e:
                # Silently handle auto function call setup errors
                pass
            
            # Create message using hub-based API
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=user_message,
            )
            logger.info(f"[AgentCore] Message created for thread ID: {self.thread.id}")

            stream_handler = StreamEventHandler(
                functions=self.functions,
                project_client=self.project_client,
                utilities=self.utilities
            )

            stream_handler.current_user_query = user_message
            
            # Skip streaming for now - use reliable non-streaming approach
            logger.info(f"[AgentCore] Using non-streaming approach for reliability")
            
            # Create run using non-streaming method (like the working simple test)
            run = await self.project_client.agents.create_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                temperature=TEMPERATURE,
            )
            logger.info(f"[AgentCore] Run started for thread ID: {self.thread.id}, Agent ID: {self.agent.id}")
            
            # Wait for run to complete
            await self._wait_for_run_completion(run.id, max_wait=60)
                
            
            # Handle ALL required actions in a loop until run completes
            runs_paged = await self.project_client.agents.list_runs(thread_id=self.thread.id)
            if hasattr(runs_paged, 'data') and runs_paged.data:
                latest_run = runs_paged.data[0]  # Most recent run
                iteration = 0
                max_iterations = 10
                
                while getattr(latest_run, 'status', None) == 'requires_action' and iteration < max_iterations:
                    iteration += 1
                    logger.info(f"[AgentCore] Iteration {iteration}: Run {latest_run.id} status: {latest_run.status}")
                    logger.info(f"[AgentCore] Handling required actions in iteration {iteration}")
                    
                    await self._handle_required_action(latest_run)
                    
                    # Get updated run status
                    await asyncio.sleep(2)  # Brief pause for processing
                    latest_run = await self.project_client.agents.get_run(
                        thread_id=self.thread.id, 
                        run_id=latest_run.id
                    )
                    logger.info(f"[AgentCore] After iteration {iteration}: Run {latest_run.id} status: {latest_run.status}")
                
                if iteration >= max_iterations:
                    logger.warning(f"[AgentCore] Reached maximum iterations ({max_iterations}) for handling required actions")
                else:
                    logger.info(f"[AgentCore] Run {latest_run.id} finished with status: {latest_run.status}")
            
            # Stream handler state diagnostics removed for cleaner output

            # Debug logging removed - thread messages and runs are processed silently

            # Always try to get the latest assistant message from the thread first
            # This ensures we get the final response after tool execution
            response_text = ""
            try:
                thread_messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
                if hasattr(thread_messages, 'data') and thread_messages.data:
                    # Look for the most recent assistant message (check for both 'assistant' and 'agent' roles)
                    # Process messages in reverse order since they might be chronologically ordered
                    for message in thread_messages.data:
                        message_role = getattr(message, 'role', None)
                        logger.debug(f"[AgentCore] Processing message role: {message_role}, type: {type(message_role)}")
                        
                        # Check for different possible role values - agent messages are assistant responses
                        if (str(message_role) in ['assistant', 'agent'] or 
                            str(message_role).endswith('AGENT') or 
                            str(message_role).endswith('ASSISTANT') or
                            message_role == MessageRole.AGENT):
                            content = getattr(message, 'content', [])
                            message_text = ""
                            for content_item in content:
                                if hasattr(content_item, 'text') and content_item.text:
                                    if hasattr(content_item.text, 'value'):
                                        message_text = content_item.text.value
                                    else:
                                        message_text = str(content_item.text)
                                    break  # Take first text content
                                        
                            # Only use this message if it's not echoing user input and has content
                            if message_text and message_text.strip() and message_text.strip().lower() != user_message.strip().lower():
                                response_text = message_text  # Use the latest response
                                # Found assistant response
                                break  # Stop at the first valid assistant message
                else:
                    # Handle async iterator
                    messages_list = []
                    async for message in thread_messages:
                        messages_list.append(message)
                    
                    # Process messages in reverse order (most recent first)
                    for message in messages_list:
                        message_role = getattr(message, 'role', None)
                        logger.debug(f"[AgentCore] Processing message role (async): {message_role}, type: {type(message_role)}")
                        
                        # Check for different possible role values - agent messages are assistant responses
                        if (str(message_role) in ['assistant', 'agent'] or 
                            str(message_role).endswith('AGENT') or 
                            str(message_role).endswith('ASSISTANT') or
                            message_role == MessageRole.AGENT):
                            content = getattr(message, 'content', [])
                            message_text = ""
                            for content_item in content:
                                if hasattr(content_item, 'text') and content_item.text:
                                    if hasattr(content_item.text, 'value'):
                                        message_text = content_item.text.value
                                    else:
                                        message_text = str(content_item.text)
                                    break  # Take first text content
                                        
                            # Only use this message if it's not echoing user input and has content
                            if message_text and message_text.strip() and message_text.strip().lower() != user_message.strip().lower():
                                response_text = message_text  # Use the latest response
                                # Found assistant response (async)
                                break  # Stop at the first valid assistant message
            except Exception as e:
                logger.warning(f"[AgentCore] Could not fetch latest message: {e}")
            
            # If we couldn't get response from thread, fallback to stream handler
            if not response_text.strip():
                response_text = (
                    getattr(stream_handler, "captured_response", None)
                    or getattr(stream_handler, "current_response_text", "")
                )
            
            # If still no response, check if there was an error and provide a helpful message
            if not response_text.strip():
                # Check the latest run for errors
                try:
                    runs_paged = await self.project_client.agents.list_runs(thread_id=self.thread.id)
                    if hasattr(runs_paged, 'data') and runs_paged.data:
                        latest_run = runs_paged.data[0]
                        if getattr(latest_run, 'status', None) == 'failed':
                            last_error = getattr(latest_run, 'last_error', {})
                            error_msg = last_error.get('message', 'Unknown error occurred')
                            response_text = f"I apologize, but I encountered an error while processing your request: {error_msg}. Please try rephrasing your question or try again."
                        elif getattr(latest_run, 'status', None) == 'requires_action':
                            response_text = "I'm still processing your request. The system requires additional actions that are being handled. Please wait a moment and try again."
                        else:
                            response_text = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question or try again."
                    else:
                        response_text = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question or try again."
                except Exception as e:
                    logger.warning(f"[AgentCore] Could not check run status: {e}")
                    response_text = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question or try again."
            
            return True, response_text
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"[AgentCore] Error processing message: {error_msg}")
            return False, error_msg
        finally:
            self._operation_active = False
            # Operation completed

    async def _handle_required_action(self, run):
        """Handle runs that require action (tool calls)."""
        try:
            import json
            if hasattr(run, 'required_action') and run.required_action:
                required_action = run.required_action
                if hasattr(required_action, 'submit_tool_outputs') and required_action.submit_tool_outputs:
                    tool_calls = required_action.submit_tool_outputs.tool_calls
                    # Handle tool calls
                    tool_outputs = []
                    for tool_call in tool_calls:
                        if tool_call.type == "function":
                            function_name = tool_call.function.name
                            function_args = tool_call.function.arguments
                            
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
                                elif function_name == "_async_fetch_org_structure":
                                    result = await self._async_fetch_org_structure()
                                elif function_name == "get_user_groups":
                                    result = await self.get_user_groups(args.get("user_id", ""))
                                elif function_name == "get_user_booking_entity":
                                    result = await self.get_user_booking_entity(args.get("user_id", ""))
                                elif function_name == "get_user_details":
                                    result = self.get_user_details(args.get("user_id", ""))
                                elif function_name == "schedule_event_with_permissions":
                                    result = await self.schedule_event_with_permissions(
                                        args.get("user_id", ""),
                                        args.get("entity_type", ""),
                                        args.get("entity_name", ""),
                                        args.get("room_id", ""),
                                        args.get("title", ""),
                                        args.get("start_time", ""),
                                        args.get("end_time", ""),
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
                                # Function executed
                                # Tool output captured
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
        """Wait for a run to reach completion or requires_action after tool outputs are submitted."""
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
                    logger.info(f"[AgentCore] Run {run_id} requires more actions - will handle in next iteration")
                    break  # Let the main loop handle the next action
                
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
            # Properly clean up MCP client HTTP sessions
            try:
                await self.mcp_client.close()
                logger.info("[AgentCore] MCP client cleaned up successfully")
            except Exception as e:
                logger.warning(f"[AgentCore] Error cleaning up MCP client: {e}")
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
