"""
Async wrapper for compat_sql_store.py
Provides async versions of the SQL store functions for use in the MCP server.
"""
import asyncio
from compat_sql_store import get_rooms, list_events, create_event, update_event, cancel_event, check_availability


async def async_get_rooms():
    """Async wrapper for get_rooms()"""
    return await asyncio.to_thread(get_rooms)


async def async_list_events(calendar_id: str):
    """Async wrapper for list_events()"""
    return await asyncio.to_thread(list_events, calendar_id)


async def async_create_event(ev: dict):
    """Async wrapper for create_event()"""
    return await asyncio.to_thread(create_event, ev)


async def async_update_event(event_id: str, patch: dict, requester_email: str):
    """Async wrapper for update_event()"""
    return await asyncio.to_thread(update_event, event_id, patch, requester_email)


async def async_cancel_event(event_id: str, requester_email: str):
    """Async wrapper for cancel_event()"""
    return await asyncio.to_thread(cancel_event, event_id, requester_email)


async def async_check_availability(calendar_id: str, start_iso: str, end_iso: str, exclude_event_id: str = None) -> bool:
    """Async wrapper for check_availability()"""
    return await asyncio.to_thread(check_availability, calendar_id, start_iso, end_iso, exclude_event_id)


async def async_get_all_events():
    """Get all events from all calendars/rooms"""
    # Get all rooms first
    rooms_data = await async_get_rooms()
    all_events = []
    
    # Collect events from all rooms
    for room in rooms_data.get("rooms", []):
        room_events = await async_list_events(room["id"])
        all_events.extend(room_events.get("events", []))
    
    return {"events": all_events}
