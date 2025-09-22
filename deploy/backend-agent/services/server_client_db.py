"""
Calendar Client using direct database access instead of HTTP.
This replaces the HTTP-based server_client.py for the deployed version.
"""

import json
import logging
from typing import Optional
from .async_sql_store import (
    async_get_rooms, 
    async_list_events, 
    async_create_event, 
    async_update_event,
    async_cancel_event,
    async_check_availability,
    async_get_all_events
)

logger = logging.getLogger(__name__)


class CalendarClient:
    """Client for interacting with the Calendar database directly."""

    def __init__(self):
        """Initialize the calendar client."""
        pass
    
    async def close(self):
        """Compatibility method - no cleanup needed for direct DB access."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def health_check(self) -> dict:
        """Check the health of the database connection."""
        try:
            # Try a simple database query to check connectivity
            rooms = await async_get_rooms()
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def list_events(self, calendar_id: str) -> dict:
        """List events for a calendar or all calendars."""
        try:
            if calendar_id == "all":
                # Get all events from all calendars
                result = await async_get_all_events()
                return {"success": True, "events": result.get("events", [])}
            else:
                # Get events for specific calendar
                result = await async_list_events(calendar_id)
                return {"success": True, "events": result.get("events", [])}
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_rooms(self) -> dict:
        """Get available rooms/calendars."""
        try:
            result = await async_get_rooms()
            return {"success": True, "rooms": result.get("rooms", [])}
        except Exception as e:
            logger.error(f"Failed to get rooms: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_event(
        self, 
        user_id: str, 
        calendar_id: str, 
        title: str, 
        start_time: str, 
        end_time: str, 
        location: Optional[str] = None, 
        description: Optional[str] = None,
        organizer: Optional[str] = None,
        attendees: Optional[list] = None
    ) -> dict:
        """Create an event in the database."""
        try:
            event_data = {
                "calendar_id": calendar_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "description": description or "",
                "organizer": organizer or user_id,
                "attendees": attendees or []
            }
            
            result = await async_create_event(event_data)
            if result:
                return {"success": True, "event": result}
            else:
                return {"success": False, "error": "Failed to create event"}
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_event(
        self,
        event_id: str,
        requester_email: str,
        patch: dict
    ) -> dict:
        """Update an event in the database."""
        try:
            result = await async_update_event(event_id, patch, requester_email)
            if result:
                return {"success": True, "event": result}
            else:
                return {"success": False, "error": "Failed to update event"}
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_event(
        self,
        event_id: str,
        requester_email: str
    ) -> dict:
        """Cancel an event in the database."""
        try:
            result = await async_cancel_event(event_id, requester_email)
            if result:
                return {"success": True, "event": result}
            else:
                return {"success": False, "error": "Failed to cancel event"}
        except Exception as e:
            logger.error(f"Failed to cancel event: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_availability(
        self,
        calendar_id: str,
        start_time: str,
        end_time: str,
        exclude_event_id: Optional[str] = None
    ) -> dict:
        """Check if a time slot is available."""
        try:
            available = await async_check_availability(
                calendar_id, start_time, end_time, exclude_event_id
            )
            return {"success": True, "available": available}
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return {"success": False, "error": str(e)}


# Keep the standalone functions for backward compatibility
async def create_event_via_mcp(*args, **kwargs):
    """Create event via MCP - uses database directly."""
    client = CalendarClient()
    return await client.create_event(*args, **kwargs)


async def list_events_via_mcp(calendar_id: str):
    """List events via MCP - uses database directly."""
    client = CalendarClient()
    return await client.list_events(calendar_id)


async def get_rooms_via_mcp():
    """Get rooms via MCP - uses database directly."""
    client = CalendarClient()
    return await client.get_rooms()