import httpx
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# MCP Server Configuration
MCP_BASE_URL = "http://localhost:8000"  # or container/service URL in deployment


class CalendarMCPClient:
    """Client for interacting with the Calendar MCP Server."""
    
    def __init__(self, base_url: str = MCP_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    async def create_event_via_mcp(
        self, 
        user_id: str, 
        calendar_id: str, 
        title: str, 
        start_time: str, 
        end_time: str, 
        location: Optional[str] = None, 
        description: Optional[str] = None
    ) -> dict:
        """Create an event via the MCP server."""
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
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
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
    
    async def list_events_via_mcp(self, calendar_id: str) -> dict:
        """List events via the MCP server."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
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
    
    async def get_rooms_via_mcp(self) -> dict:
        """Get available calendars via the MCP server."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
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
    
    async def check_room_availability_via_mcp(
        self, 
        room_id: str, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """Check calendar availability via the MCP server."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
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
        """Check if the MCP server is healthy."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
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


# Convenience functions for backward compatibility
async def create_event_via_mcp(user_id: str, calendar_id: str, title: str, start_time: str, end_time: str, location: str = None, description: str = None):
    """Convenience function for creating events via MCP."""
    client = CalendarMCPClient()
    return await client.create_event_via_mcp(user_id, calendar_id, title, start_time, end_time, location, description)

async def list_events_via_mcp(calendar_id: str):
    """Convenience function for listing events via MCP."""
    client = CalendarMCPClient()
    return await client.list_events_via_mcp(calendar_id)

async def get_rooms_via_mcp():
    """Convenience function for getting rooms via MCP."""
    client = CalendarMCPClient()
    return await client.get_rooms_via_mcp()

async def check_room_availability_via_mcp(room_id: str, start_time: str, end_time: str):
    """Convenience function for checking room availability via MCP."""
    client = CalendarMCPClient()
    return await client.check_room_availability_via_mcp(room_id, start_time, end_time)
