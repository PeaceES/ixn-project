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

app = FastAPI(title="Enhanced Calendar MCP Server", version="2.0.0")

# Global storage
rooms_data = {}
events_data = {"events": []}
user_directory = {}

# File paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'json')
ROOMS_FILE = os.path.join(DATA_DIR, "rooms.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
USER_DIRECTORY_LOCAL_FILE = os.path.join(DATA_DIR, "user_directory_local.json")
USER_DIRECTORY_URL = os.getenv("USER_DIRECTORY_URL")

# Request schema
class CreateEventRequest(BaseModel):
    user_id: str
    group_id: str  # Changed from calendar_id to group_id
    room_id: str   # Added explicit room_id
    title: str
    start_time: str  # ISO 8601 format
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None


# Utility functions
async def load_rooms():
    """Load rooms configuration from JSON file."""
    global rooms_data
    try:
        with open(ROOMS_FILE, 'r') as f:
            rooms_data = json.load(f)
        print(f"✅ Loaded {len(rooms_data.get('rooms', []))} rooms from {ROOMS_FILE}")
    except FileNotFoundError:
        print(f"⚠️ {ROOMS_FILE} not found, using empty rooms list")
        rooms_data = {"rooms": []}
    except Exception as e:
        print(f"❌ Error loading rooms: {e}")
        rooms_data = {"rooms": []}


async def load_events():
    """Load events from JSON file."""
    global events_data
    try:
        with open(EVENTS_FILE, 'r') as f:
            events_data = json.load(f)
        print(f"✅ Loaded {len(events_data.get('events', []))} events from {EVENTS_FILE}")
    except FileNotFoundError:
        print(f"⚠️ {EVENTS_FILE} not found, creating empty events file")
        events_data = {"events": []}
        await save_events()
    except Exception as e:
        print(f"❌ Error loading events: {e}")
        events_data = {"events": []}


async def save_events():
    """Save events to JSON file."""
    try:
        with open(EVENTS_FILE, 'w') as f:
            json.dump(events_data, f, indent=2)
        print(f"💾 Saved {len(events_data.get('events', []))} events to {EVENTS_FILE}")
    except Exception as e:
        print(f"❌ Error saving events: {e}")


async def load_user_directory():
    """Load user directory from local file first, then Azure blob as fallback."""
    global user_directory
    
    # Try local file first
    try:
        with open(USER_DIRECTORY_LOCAL_FILE, 'r') as f:
            user_directory = json.load(f)
        print(f"✅ Loaded {len(user_directory)} users from local file")
        return
    except FileNotFoundError:
        print(f"⚠️ {USER_DIRECTORY_LOCAL_FILE} not found, trying remote URL")
    except Exception as e:
        print(f"❌ Error loading local user directory: {e}")
    
    # Fallback to remote URL
    if not USER_DIRECTORY_URL:
        print("⚠️ USER_DIRECTORY_URL not configured, using empty user directory")
        user_directory = {}
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(USER_DIRECTORY_URL, timeout=10)
            response.raise_for_status()
            user_directory = response.json()
        print(f"✅ Loaded {len(user_directory)} users from remote URL")
    except Exception as e:
        print(f"⚠️ Failed to load remote user directory: {e}")
        user_directory = {}


def validate_user_exists(user_id: str) -> tuple[bool, str, dict]:
    """Validate if user exists in directory."""
    if not user_directory:
        # If no user directory, allow all operations (fallback mode)
        return True, "No user directory configured, allowing access", {}
    
    user_info = user_directory.get(user_id)
    if not user_info:
        return False, f"User '{user_id}' not found in directory", {}
    
    return True, "User found", user_info


def validate_room_exists(room_id: str) -> tuple[bool, str, dict]:
    """Validate if room exists and return room info."""
    for room in rooms_data.get("rooms", []):
        if room["id"] == room_id:
            return True, "Room found", room
    
    return False, f"Room '{room_id}' not found", {}


def check_time_conflicts(calendar_id: str, start_time: str, end_time: str, exclude_event_id: str = None) -> tuple[bool, list]:
    """Check for time conflicts with existing events in the same calendar."""
    try:
        new_start = parser.parse(start_time)
        new_end = parser.parse(end_time)
    except Exception:
        return True, ["Invalid date format"]
    
    conflicts = []
    for event in events_data.get("events", []):
        if event.get("calendar_id") != calendar_id:
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
                    "start_time": event["start_time"],
                    "end_time": event["end_time"]
                })
        except Exception:
            continue
    
    return len(conflicts) > 0, conflicts


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


@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server with data from files."""
    print("Starting Enhanced Calendar MCP Server...")
    await load_rooms()
    await load_events()
    await load_user_directory()
    print("Enhanced Calendar MCP Server ready!")


@app.post("/calendars/{calendar_id}/events")
async def create_event(calendar_id: str, payload: CreateEventRequest):
    """Create a new calendar event with full validation."""
    try:
        # 1. Validate user permissions
        has_permission, permission_msg = validate_user_permissions(payload.user_id, calendar_id)
        if not has_permission:
            raise HTTPException(status_code=403, detail=permission_msg)
        
        # 2. Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # 3. Validate required fields
        if not payload.title or not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="Missing required fields: title, start_time, end_time")
        
        # 4. Check for time conflicts
        has_conflicts, conflicts = check_time_conflicts(calendar_id, payload.start_time, payload.end_time)
        if has_conflicts:
            conflict_details = [f"'{c['title']}' ({c['start_time']} - {c['end_time']})" for c in conflicts]
            raise HTTPException(
                status_code=409, 
                detail=f"Time conflict with existing events: {', '.join(conflict_details)}"
            )
        
        # 5. Create the event
        event = {
            "id": str(uuid.uuid4()),
            "calendar_id": calendar_id,
            "calendar_name": calendar_info.get("name", calendar_id),
            "title": payload.title,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
            "organizer": payload.user_id,
            "location": payload.location or calendar_info.get("location", ""),
            "description": payload.description or "",
            "created_at": datetime.utcnow().isoformat(),
            "attendees": [payload.user_id],
            "status": "confirmed"
        }
        
        # 6. Save event
        events_data["events"].append(event)
        await save_events()
        
        return {
            "success": True,
            "event": event,
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
            return {
                "success": True,
                "events": events_data.get("events", []),
                "calendar_id": "all",
                "calendar_name": "All Calendars",
                "total_events": len(events_data.get("events", []))
            }
        
        # Validate calendar exists
        calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
        if not calendar_exists:
            raise HTTPException(status_code=404, detail=calendar_msg)
        
        # Filter events by calendar
        calendar_events = [
            event for event in events_data.get("events", [])
            if event.get("calendar_id") == calendar_id
        ]
        
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
        return {
            "success": True,
            "events": events_data.get("events", []),
            "total_events": len(events_data.get("events", []))
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
        
        # Get event count for this calendar
        event_count = len([
            event for event in events_data.get("events", [])
            if event.get("calendar_id") == calendar_id
        ])
        
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
        has_conflicts, conflicts = check_time_conflicts(calendar_id, start_time, end_time)
        
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
