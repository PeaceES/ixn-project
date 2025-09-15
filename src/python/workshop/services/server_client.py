import httpx
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Calendar Server Configuration
CALENDAR_BASE_URL = "http://localhost:8000"  # or container/service URL in deployment


class CalendarClient:
    """Client for interacting with the Calendar Server."""

    def __init__(self, base_url: str = CALENDAR_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with proper session management."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client session properly."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("[Calendar Client] HTTP session closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
    
    async def create_event(
        self, 
        user_id: str, 
        calendar_id: str, 
        title: str, 
        start_time: str, 
        end_time: str, 
        location: Optional[str] = None, 
        description: Optional[str] = None
    ) -> dict:
        """Create an event via the calendar server."""
        payload = {
            "user_id": user_id,
            "calendar_id": calendar_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "description": description
        }
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/calendars/{calendar_id}/events", 
                json=payload,
                timeout=30.0
            )
            if response.status_code == 403:
                return {"success": False, "error": "Permission denied"}
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Invalid request data")
                return {"success": False, "error": error_detail}
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def list_events(self, calendar_id: str) -> dict:
        """List events via the calendar server."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/calendars/{calendar_id}/events",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def get_rooms(self) -> dict:
        """Get available calendars via the calendar server."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/calendars",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def check_room_availability(
        self,
        room_id: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """Check calendar availability via the calendar server."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/calendars/{room_id}/availability",
                params={
                    "start_time": start_time,
                    "end_time": end_time
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def health_check(self) -> dict:
        """Check if the calendar server is healthy."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/health",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"status": "unhealthy", "error": "Health check timeout"}
        except httpx.RequestError as e:
            return {"status": "unhealthy", "error": f"Network error: {e}"}
        except Exception as e:
            return {"status": "unhealthy", "error": f"Health check failed: {e}"}
    
    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """Update an existing event via the calendar server."""
        payload = {}
        if user_id is not None:
            payload["user_id"] = user_id
        if title is not None:
            payload["title"] = title
        if start_time is not None:
            payload["start_time"] = start_time
        if end_time is not None:
            payload["end_time"] = end_time
        if location is not None:
            payload["location"] = location
        if description is not None:
            payload["description"] = description
        
        try:
            client = await self._get_client()
            response = await client.put(
                f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 403:
                return {"success": False, "error": "Permission denied"}
            elif response.status_code == 404:
                return {"success": False, "error": "Event not found"}
            elif response.status_code == 409:
                return {"success": False, "error": "Time conflict with existing events"}
            
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def delete_event(self, calendar_id: str, event_id: str, user_id: str = None) -> dict:
        """Delete an existing event via the calendar server."""
        try:
            client = await self._get_client()
            params = {}
            if user_id:
                params["user_id"] = user_id
                
            response = await client.delete(
                f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                params=params,
                timeout=30.0
            )
            
            if response.status_code == 404:
                return {"success": False, "error": "Event not found"}
            
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    async def get_event(self, calendar_id: str, event_id: str) -> dict:
        """Get event details via the calendar server."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                timeout=30.0
            )
            if response.status_code == 404:
                return {"success": False, "error": "Event not found"}
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

    async def find_event_calendar(self, event_id: str) -> dict:
        """Find which calendar contains the given event ID."""
        try:
            # Get all calendars
            calendars_result = await self.get_rooms()
            if not calendars_result.get("success", True):
                return {"success": False, "error": "Cannot retrieve calendars"}
            
            calendars = calendars_result.get("calendars", [])
            if not calendars:
                return {"success": False, "error": "No calendars available"}
            
            # Search for the event in each calendar
            for calendar in calendars:
                calendar_id = calendar.get("id")
                if not calendar_id:
                    continue
                    
                # Try to get the event from this calendar
                event_result = await self.get_event(calendar_id, event_id)
                if event_result.get("success", True) and "error" not in event_result:
                    # Found the event!
                    return {
                        "success": True,
                        "calendar_id": calendar_id,
                        "event": event_result
                    }
            
            # Event not found in any calendar
            return {"success": False, "error": f"Event '{event_id}' not found in any calendar"}
            
        except Exception as e:
            return {"success": False, "error": f"Error searching for event: {e}"}


# Convenience functions for backward compatibility
async def create_event_via_mcp(user_id: str, calendar_id: str, title: str, start_time: str, end_time: str, location: str = None, description: str = None):
    """Convenience function for creating events via calendar server."""
    client = CalendarClient()
    return await client.create_event(user_id, calendar_id, title, start_time, end_time, location, description)

async def list_events_via_mcp(calendar_id: str):
    """Convenience function for listing events via calendar server."""
    client = CalendarClient()
    return await client.list_events(calendar_id)

async def get_rooms_via_mcp():
    """Convenience function for getting rooms via calendar server."""
    client = CalendarClient()
    return await client.get_rooms()

async def check_room_availability_via_mcp(room_id: str, start_time: str, end_time: str):
    """Convenience function for checking room availability via calendar server."""
    client = CalendarClient()
    return await client.check_room_availability(room_id, start_time, end_time)

async def update_event(calendar_id: str, event_id: str, user_id: str = None, title: str = None, 
                              start_time: str = None, end_time: str = None, location: str = None, description: str = None):
    """Convenience function for updating events via calendar server."""
    client = CalendarClient()
    return await client.update_event(calendar_id, event_id, user_id, title, start_time, end_time, location, description)

async def delete_event_via_mcp(calendar_id: str, event_id: str, user_id: str = None):
    """Convenience function for deleting events via calendar server."""
    client = CalendarClient()
    return await client.delete_event(calendar_id, event_id, user_id)

async def get_event_via_mcp(calendar_id: str, event_id: str):
    """Convenience function for getting event details via calendar server."""
    client = CalendarClient()
    return await client.get_event(calendar_id, event_id)
