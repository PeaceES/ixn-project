from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import os
import httpx
from datetime import datetime, timedelta
from dateutil import parser
import uuid
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from async_sql_store import async_get_rooms, async_list_events, async_create_event, async_update_event, async_cancel_event, async_check_availability, async_get_all_events

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the MCP server with data from files on startup."""
    print("Starting Enhanced Calendar MCP Server...")
    
    # Load rooms first (required for calendars)
    await load_rooms()
    
    # Load calendars (creates room-based calendars)
    await load_calendars()
    
    # Load events
    await load_events()
    
    # Load user directory
    await load_user_directory()
    
    print("Enhanced Calendar MCP Server ready!")
    yield
    # Cleanup can go here if needed

app = FastAPI(title="Enhanced Calendar MCP Server", version="2.0.0", lifespan=lifespan)

# Global storage
rooms_data = {}
calendars_data = {}  # Room-based calendars
events_data = {"events": []}
user_directory = {}

# File paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'json')
ROOMS_FILE = os.path.join(DATA_DIR, "rooms.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
USER_DIRECTORY_LOCAL_FILE = os.path.join(DATA_DIR, "user_directory_local.json")
USER_DIRECTORY_URL = os.getenv("USER_DIRECTORY_URL")

# Request schemas
class CreateEventRequest(BaseModel):
    user_id: str
    calendar_id: str  # This will be the room_id (simplified)
    title: str
    start_time: str  # ISO 8601 format
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None


class UpdateEventRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[str] = None  # ISO 8601 format
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


# Utility functions
async def load_rooms():
    """Load rooms configuration from SQL database."""
    global rooms_data
    try:
        rooms_data = await async_get_rooms()
        print(f"✅ Loaded {len(rooms_data.get('rooms', []))} rooms from database")
    except Exception as e:
        print(f"❌ Error loading rooms from database: {e}")
        rooms_data = {"rooms": []}


async def load_calendars():
    """Load calendars - simplified to only use rooms as calendars."""
    global calendars_data
    try:
        # Create calendars based on rooms (each room is essentially a calendar)
        calendars = []
        for room in rooms_data.get("rooms", []):
            calendars.append({
                "id": room["id"],
                "name": room.get("name", f"Room {room['id']}"),
                "type": "room",
                "location": room.get("location", ""),
                "capacity": room.get("capacity", 0)
            })
        
        calendars_data = {"calendars": calendars}
        print(f"Created {len(calendars)} room-based calendars")
        
    except Exception as e:
        print(f"Error creating calendars from rooms: {e}")
        calendars_data = {"calendars": []}
    except Exception as e:
        print(f"Error loading calendars: {e}")
        calendars_data = {"calendars": []}


async def load_events():
    """Load events from SQL database."""
    global events_data
    try:
        events_data = await async_get_all_events()
        print(f"✅ Loaded {len(events_data.get('events', []))} events from database")
    except Exception as e:
        print(f"❌ Error loading events from database: {e}")
        events_data = {"events": []}


async def save_events():
    """Save events - No longer needed as events are saved directly to database."""
    # Events are now saved directly to the database via the SQL adapter
    # This function is kept for compatibility but is now a no-op
    print("💾 Events are saved automatically to database")


async def load_user_directory():
    """Load user directory from local file first, then Azure blob as fallback."""
    global user_directory
    
    # Try local file first
    try:
        with open(USER_DIRECTORY_LOCAL_FILE, 'r') as f:
            user_directory = json.load(f)
        print(f"Loaded {len(user_directory)} users from local file")
        return
    except FileNotFoundError:
        print(f"Warning: {USER_DIRECTORY_LOCAL_FILE} not found, trying remote URL")
    except Exception as e:
        print(f"Error loading local user directory: {e}")
    
    # Fallback to remote URL
    if not USER_DIRECTORY_URL:
        print("Warning: USER_DIRECTORY_URL not configured, using empty user directory")
        user_directory = {}
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(USER_DIRECTORY_URL, timeout=10)
            response.raise_for_status()
            user_directory = response.json()
        print(f"Loaded {len(user_directory)} users from remote URL")
    except Exception as e:
        print(f"Warning: Failed to load remote user directory: {e}")
        user_directory = {}


def validate_user_exists(user_id: str) -> tuple[bool, str, dict]:
    """Validate if user exists in org structure with flexible matching."""
    # Load org structure
    org_data = load_org_structure()
    if not org_data:
        return False, "Organization structure not available", {}
    
    users = org_data.get('users', [])
    
    # Try matching by ID (as string)
    try:
        user_id_int = int(user_id)
        for user in users:
            if user.get('id') == user_id_int:
                return True, "User found", user
    except ValueError:
        pass
    
    # Try matching by email
    for user in users:
        if user.get('email', '').lower() == user_id.lower():
            return True, "User found", user
    
    # Try matching by name
    for user in users:
        if user.get('name', '').lower() == user_id.lower():
            return True, "User found", user
    
    return False, f"User '{user_id}' not found in organization", {}


def load_org_structure() -> dict:
    """Load the organization structure from JSON file."""
    import os, json
    try:
        org_path = os.path.join(os.path.dirname(__file__), '../../../shared/database/data-generator/org_structure.json')
        with open(org_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load org_structure.json: {e}")
        return {}


def validate_group_exists(group_id: str) -> tuple[bool, str, dict]:
    """Validate if group exists - disabled since we removed group calendars."""
    return False, f"Group calendars are disabled", {}


def validate_room_exists(room_id: str) -> tuple[bool, str, dict]:
    """Validate if room exists and return room info."""
    for room in rooms_data.get("rooms", []):
        if room["id"] == room_id:
            return True, "Room found", room
    
    return False, f"Room '{room_id}' not found", {}


def validate_user_permissions(user_id: str, calendar_id: str) -> tuple[bool, str]:
    """Validate if user has permission to access the calendar based on org structure."""
    user_exists, user_msg, user_info = validate_user_exists(user_id)
    if not user_exists:
        return False, user_msg
    
    # In the new org structure, everyone can book as long as they're booking for the right entity:
    # - Department staff/admin can book for any course or society in their department
    # - Society officers can only book for their own society
    return True, "User has booking permissions based on organizational role"


def can_user_book_for_entity(user_id: str, entity_type: str, entity_id: int) -> tuple[bool, str]:
    """Check if user can book for a specific entity (department, course, society)."""
    user_exists, user_msg, user_info = validate_user_exists(user_id)
    if not user_exists:
        return False, user_msg
    
    org_data = load_org_structure()
    if not org_data:
        return False, "Organization structure not available"
    
    user_role = user_info.get('role_scope', '')
    user_dept_id = user_info.get('department_id')
    user_scope_id = user_info.get('scope_id')
    
    if user_role in ['department', 'staff']:
        # Department staff can book for any course or society in their department
        if entity_type == 'department' and entity_id == user_dept_id:
            return True, "Department member can book for their department"
        elif entity_type == 'course':
            # Check if course belongs to user's department
            courses = org_data.get('courses', [])
            for course in courses:
                if course.get('id') == entity_id and course.get('department_id') == user_dept_id:
                    return True, "Department member can book for department courses"
        elif entity_type == 'society':
            # Check if society belongs to user's department
            societies = org_data.get('societies', [])
            for society in societies:
                if society.get('id') == entity_id and society.get('department_id') == user_dept_id:
                    return True, "Department member can book for department societies"
    
    elif user_role == 'society_officer':
        # Society officers can only book for their own society
        if entity_type == 'society' and entity_id == user_scope_id:
            return True, "Society officer can book for their own society"
    
    return False, f"User does not have permission to book for {entity_type} {entity_id}"


def extract_entity_from_description(description: str) -> Optional[str]:
    """Extract the entity name from description that contains 'organized by'."""
    import re
    
    # First check for "organized by X for Y" pattern - we want Y
    for_pattern = r"organized by .+? for (?:the )?(.+?)(?:\.|,|$)"
    match = re.search(for_pattern, description, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Otherwise check standard patterns
    patterns = [
        r"organized by the (.+?)(?:\.|,|$)",  # "organized by the AI Society."
        r"organized by (.+?)(?:\.|,|$)",       # "organized by AI Society"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def find_entity_email(entity_name: str) -> Optional[str]:
    """Find the email address for an entity (department, society, course) from org structure."""
    if not entity_name:
        return None
        
    org_data = load_org_structure()
    if not org_data:
        return None
    
    # Normalize the entity name for comparison
    normalized_name = entity_name.lower().strip()
    
    # Check departments
    for dept in org_data.get('departments', []):
        if dept.get('name', '').lower() == normalized_name:
            return dept.get('email')
    
    # Check societies
    for society in org_data.get('societies', []):
        if society.get('name', '').lower() == normalized_name:
            return society.get('email')
    
    # Check courses
    for course in org_data.get('courses', []):
        if course.get('name', '').lower() == normalized_name:
            return course.get('email')
    
    return None


def validate_calendar_exists(calendar_id: str) -> tuple[bool, str, dict]:
    """Validate if calendar exists and return calendar info - simplified for room-only system."""
    # Check in room-based calendars
    for calendar in calendars_data.get("calendars", []):
        if calendar["id"] == calendar_id:
            return True, "Calendar found", calendar
    
    return False, f"Calendar '{calendar_id}' not found", {}


async def check_time_conflicts(calendar_id: str, start_time: str, end_time: str, exclude_event_id: str = None) -> tuple[bool, list]:
    """Check for time conflicts with existing events in the same calendar using database."""
    try:
        # Use the SQL adapter to check availability
        is_available = await async_check_availability(calendar_id, start_time, end_time, exclude_event_id)
        
        if is_available:
            return False, []  # No conflicts
        else:
            # If not available, get the actual conflicts by fetching events for this calendar
            calendar_events_data = await async_list_events(calendar_id)
            events = calendar_events_data.get("events", [])
            
            try:
                new_start = parser.parse(start_time)
                new_end = parser.parse(end_time)
            except Exception:
                return True, ["Invalid date format"]
            
            conflicts = []
            for event in events:
                if exclude_event_id and event.get("id") == exclude_event_id:
                    continue
                
                try:
                    event_start = parser.parse(event["start_time"])
                    event_end = parser.parse(event["end_time"])
                    
                    # Check for overlap
                    if (new_start < event_end) and (new_end > event_start):
                        conflicts.append({
                            "event_id": event.get("id"),
                            "title": event.get("title"),
                            "start_time": event["start_time"],
                            "end_time": event["end_time"]
                        })
                except Exception:
                    continue
            
            return True, conflicts
    except Exception as e:
        print(f"Error checking time conflicts: {e}")
        return True, ["Database error occurred"]


def check_room_conflicts(room_id: str, start_time: str, end_time: str, exclude_event_id: str = None) -> tuple[bool, list]:
    """Check for time conflicts with existing events in the same room."""
    try:
        new_start = parser.parse(start_time)
        new_end = parser.parse(end_time)
    except Exception:
        return True, ["Invalid date format"]
    
    conflicts = []
    for event in events_data.get("events", []):
        if event.get("room_id") != room_id:
            continue
        
        if exclude_event_id and event.get("id") == exclude_event_id:
            continue
        
        try:
            event_start = parser.parse(event["start_time"])
            event_end = parser.parse(event["end_time"])
            
            # Check for overlap
            if (new_start < event_end) and (new_end > event_start):
                conflicts.append({
                    "event_id": event.get("id"),
                    "title": event.get("title"),
                    "group_id": event.get("group_id"),
                    "start_time": event["start_time"],
                    "end_time": event["end_time"]
                })
        except Exception:
            continue
    
    return len(conflicts) > 0, conflicts


@app.post("/calendars/{calendar_id}/events")
async def create_event(calendar_id: str, payload: CreateEventRequest):
    """Create a new calendar event with full validation."""
    try:
        # 1. Validate user exists and get user info
        user_exists, user_msg, user_info = validate_user_exists(payload.user_id)
        if not user_exists:
            raise HTTPException(status_code=404, detail=user_msg)
        
        # 2. Validate user permissions
        has_permission, permission_msg = validate_user_permissions(payload.user_id, calendar_id)
        if not has_permission:
            raise HTTPException(status_code=403, detail=permission_msg)
        
        # 3. Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # 4. Validate required fields
        if not payload.title or not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="Missing required fields: title, start_time, end_time")
        
        # 5. Check for time conflicts
        has_conflicts, conflicts = await check_time_conflicts(calendar_id, payload.start_time, payload.end_time)
        if has_conflicts:
            conflict_details = [f"'{c['title']}' ({c['start_time']} - {c['end_time']})" for c in conflicts]
            raise HTTPException(
                status_code=409, 
                detail=f"Time conflict with existing events: {', '.join(conflict_details)}"
            )
        
        # 6. Create the event
        # Extract email from user_info if we have it
        organizer_email = user_info.get('email', payload.user_id) if user_info else payload.user_id
        
        # Extract entity from description and find its email for attendees
        entity_name = extract_entity_from_description(payload.description or "")
        entity_email = find_entity_email(entity_name) if entity_name else None
        
        # Use entity email for attendees if found, otherwise use organizer email
        attendees = [entity_email] if entity_email else [organizer_email]
        
        event = {
            "id": str(uuid.uuid4()),
            "calendar_id": calendar_id,
            "calendar_name": calendar_info.get("name", calendar_id),
            "title": payload.title,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
            "organizer": organizer_email,  # Now storing email instead of ID
            "location": payload.location or calendar_info.get("location", ""),
            "description": payload.description or "",
            "created_at": datetime.utcnow().isoformat(),
            "attendees": attendees,  # Use entity email if available
            "status": "confirmed"
        }
        
        # 7. Save event to database
        created_event = await async_create_event(event)
        if not created_event:
            raise HTTPException(status_code=500, detail="Failed to create event in database")
        
        # Update global cache for immediate consistency (optional - could be removed)
        events_data["events"].append(created_event)
        
        return {
            "success": True,
            "event": created_event,
            "message": f"Event '{payload.title}' created successfully in {calendar_info.get('name', calendar_id)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/calendars/{calendar_id}/events")
async def list_events(calendar_id: str):
    """List all events for a specific calendar."""
    try:
        # Handle "all" as special case to return all events
        if calendar_id.lower() == "all":
            all_events_data = await async_get_all_events()
            return {
                "success": True,
                "events": all_events_data.get("events", []),
                "calendar_id": "all",
                "calendar_name": "All Calendars",
                "total_events": len(all_events_data.get("events", []))
            }
        
        # Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Get events from database for this calendar
        calendar_events_data = await async_list_events(calendar_id)
        calendar_events = calendar_events_data.get("events", [])
        
        return {
            "success": True,
            "events": calendar_events,
            "calendar_id": calendar_id,
            "calendar_name": calendar_info.get("name", calendar_id),
            "total_events": len(calendar_events)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/events")
async def list_all_events():
    """List all events across all calendars."""
    try:
        all_events_data = await async_get_all_events()
        return {
            "success": True,
            "events": all_events_data.get("events", []),
            "total_events": len(all_events_data.get("events", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/calendars")
async def list_calendars():
    """List all available calendars."""
    try:
        return {
            "success": True,
            "calendars": calendars_data.get("calendars", []),
            "total_calendars": len(calendars_data.get("calendars", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/calendars/{calendar_id}")
async def get_calendar_info(calendar_id: str):
    """Get detailed information about a specific calendar."""
    try:
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Get event count for this calendar from database
        calendar_events_data = await async_list_events(calendar_id)
        event_count = len(calendar_events_data.get("events", []))
        
        return {
            "success": True,
            "calendar": calendar_info,
            "event_count": event_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/calendars/{calendar_id}/availability")
async def check_calendar_availability(calendar_id: str, start_time: str, end_time: str):
    """Check if a calendar is available during a specific time period."""
    try:
        # Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Check for conflicts
        has_conflicts, conflicts = await check_time_conflicts(calendar_id, start_time, end_time)
        
        return {
            "success": True,
            "available": not has_conflicts,
            "calendar_id": calendar_id,
            "calendar_name": calendar_info.get("name", calendar_id),
            "start_time": start_time,
            "end_time": end_time,
            "conflicts": conflicts if has_conflicts else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """Get user permissions and allowed calendars."""
    try:
        if not user_directory:
            return {
                "success": True,
                "user_id": user_id,
                "permissions": "No user directory configured - all access allowed",
                "allowed_calendars": ["all"]
            }
        
        user_info = user_directory.get(user_id)
        if not user_info:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        
        return {
            "success": True,
            "user_id": user_id,
            "user_info": user_info,
            "allowed_calendars": user_info.get("allowed_calendars", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.put("/calendars/{calendar_id}/events/{event_id}")
async def update_event(calendar_id: str, event_id: str, payload: UpdateEventRequest):
    """Update an existing calendar event."""
    try:
        # Validate calendar exists first
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Get user email for permissions
        requester_email = payload.user_id
        if payload.user_id and "@" not in payload.user_id:
            # Try to get email from user validation
            user_exists, user_msg, user_info = validate_user_exists(payload.user_id)
            if user_exists:
                requester_email = user_info.get('email', payload.user_id)
        
        # Prepare patch data (only include fields that were provided)
        patch = {}
        if payload.title is not None:
            patch["title"] = payload.title
        if payload.start_time is not None:
            patch["start_time"] = payload.start_time
        if payload.end_time is not None:
            patch["end_time"] = payload.end_time
        if payload.description is not None:
            patch["description"] = payload.description
        
        # If times are being updated, check for conflicts first
        if payload.start_time or payload.end_time:
            # Get current event to determine start/end times for conflict check
            calendar_events_data = await async_list_events(calendar_id)
            current_event = None
            for event in calendar_events_data.get("events", []):
                if event.get("id") == event_id:
                    current_event = event
                    break
            
            if not current_event:
                raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found")
            
            start_time = payload.start_time or current_event["start_time"]
            end_time = payload.end_time or current_event["end_time"]
            
            # Check for conflicts, excluding the current event
            has_conflicts, conflicts = await check_time_conflicts(calendar_id, start_time, end_time, exclude_event_id=event_id)
            if has_conflicts:
                conflict_details = [f"'{c['title']}' ({c['start_time']} - {c['end_time']})" for c in conflicts]
                raise HTTPException(
                    status_code=409, 
                    detail=f"Time conflict with existing events: {', '.join(conflict_details)}"
                )
        
        # Update the event using SQL database
        updated_event = await async_update_event(event_id, patch, requester_email)
        
        if not updated_event:
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found or permission denied")
        
        # Refresh global cache by reloading events (optional - for immediate consistency)
        await load_events()
        
        return {
            "success": True,
            "event": updated_event,
            "message": f"Event '{updated_event.get('title', event_id)}' updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/calendars/{calendar_id}/events/{event_id}")
async def delete_event(calendar_id: str, event_id: str, user_id: str = None):
    """Delete an existing calendar event."""
    try:
        # Validate calendar exists first
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Get the event first to validate it exists and belongs to this calendar
        calendar_events_data = await async_list_events(calendar_id)
        event_to_delete = None
        for event in calendar_events_data.get("events", []):
            if event.get("id") == event_id:
                event_to_delete = event
                break
        
        if not event_to_delete:
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found in calendar '{calendar_id}'")
        
        # Get user email for permissions
        requester_email = user_id
        if user_id and "@" not in user_id:
            # Try to get email from user validation
            user_exists, user_msg, user_info = validate_user_exists(user_id)
            if user_exists:
                requester_email = user_info.get('email', user_id)
        
        # Cancel the event using SQL database
        # The SQL function handles permission checking internally
        cancelled_event = await async_cancel_event(event_id, requester_email)
        
        if not cancelled_event:
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found or permission denied")
        
        # Refresh global cache by reloading events (optional - for immediate consistency)
        await load_events()
        
        return {
            "success": True,
            "deleted_event_id": event_id,
            "original_event": event_to_delete,  # Include original event data
            "message": f"Event '{event_to_delete.get('title', 'Unknown Event')}' cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/calendars/{calendar_id}/events/{event_id}")
async def get_event(calendar_id: str, event_id: str):
    """Get details of a specific event."""
    try:
        # Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Get events from database for this calendar
        calendar_events_data = await async_list_events(calendar_id)
        event = None
        for e in calendar_events_data.get("events", []):
            if e.get("id") == event_id:
                event = e
                break
        
        if not event:
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found in calendar '{calendar_id}'")
        
        return {
            "success": True,
            "event": event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Enhanced Calendar MCP Server",
        "version": "2.0.0",
        "calendars_loaded": len(calendars_data.get("calendars", [])),
        "events_count": len(events_data.get("events", [])),
        "users_loaded": len(user_directory)
    }


@app.get("/rooms")
async def list_rooms():
    """List all available rooms."""
    try:
        return {
            "success": True,
            "rooms": rooms_data.get("rooms", []),
            "total_rooms": len(rooms_data.get("rooms", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
