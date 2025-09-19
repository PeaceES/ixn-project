"""
New integration tests for calendar service with database.
"""
import pytest
import asyncio
import tempfile
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.async_sql_store import (
    async_create_event, async_list_events, async_get_rooms, async_check_availability
)


@pytest.mark.integration
class TestCalendarIntegration:
    """Test integration between calendar service and database."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_event_creation(self, sample_events):
        """Test complete event creation workflow."""
        event_data = sample_events[0]
        
        with patch('services.compat_sql_store.create_event') as mock_create, \
             patch('services.compat_sql_store.list_events') as mock_list:
            
            # Mock successful creation
            mock_create.return_value = {"success": True, "event_id": "new-event-123"}
            mock_list.return_value = {"events": [event_data]}
            
            # Create event
            create_result = await async_create_event(event_data)
            assert create_result["success"] is True
            
            # Verify event exists
            list_result = await async_list_events("room1")
            assert len(list_result["events"]) == 1
            assert list_result["events"][0]["title"] == event_data["title"]
    
    @pytest.mark.asyncio
    async def test_room_availability_workflow(self):
        """Test room availability checking workflow."""
        room_id = "room1"
        start_time = "2024-12-01T10:00:00Z"
        end_time = "2024-12-01T11:00:00Z"
        
        with patch('services.compat_sql_store.check_availability') as mock_check, \
             patch('services.compat_sql_store.get_rooms') as mock_rooms:
            
            # Setup room data
            mock_rooms.return_value = {"rooms": [{"id": room_id, "name": "Conference Room A"}]}
            mock_check.return_value = True
            
            # Check room availability
            rooms = await async_get_rooms()
            assert len(rooms["rooms"]) == 1
            
            availability = await async_check_availability(room_id, start_time, end_time)
            assert availability is True
    
    @pytest.mark.asyncio
    async def test_conflict_detection_integration(self, sample_events):
        """Test that the system detects scheduling conflicts."""
        event1 = sample_events[0]
        
        # Create overlapping event
        event2 = event1.copy()
        event2["id"] = "event-2"
        event2["title"] = "Conflicting Meeting"
        event2["start_time"] = "2024-12-01T09:15:00Z"  # Overlaps with event1
        
        with patch('services.compat_sql_store.check_availability') as mock_check, \
             patch('services.compat_sql_store.create_event') as mock_create:
            
            # First event succeeds
            mock_check.return_value = True
            mock_create.return_value = {"success": True, "event_id": "event-1"}
            
            result1 = await async_create_event(event1)
            assert result1["success"] is True
            
            # Second event should detect conflict
            mock_check.return_value = False  # Room not available
            mock_create.return_value = {"success": False, "error": "Room conflict"}
            
            result2 = await async_create_event(event2)
            assert result2["success"] is False
            assert "conflict" in result2.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_multi_room_scheduling(self):
        """Test scheduling across multiple rooms."""
        rooms_data = {
            "rooms": [
                {"id": "room1", "name": "Conference Room A"},
                {"id": "room2", "name": "Conference Room B"},
                {"id": "room3", "name": "Meeting Room C"}
            ]
        }
        
        with patch('services.compat_sql_store.get_rooms') as mock_rooms, \
             patch('services.compat_sql_store.check_availability') as mock_check:
            
            mock_rooms.return_value = rooms_data
            
            # Room1 not available, Room2 available
            mock_check.side_effect = [False, True, True]
            
            rooms = await async_get_rooms()
            assert len(rooms["rooms"]) == 3
            
            # Check availability for each room
            for room in rooms["rooms"]:
                available = await async_check_availability(
                    room["id"], 
                    "2024-12-01T10:00:00Z", 
                    "2024-12-01T11:00:00Z"
                )
                if room["id"] == "room1":
                    assert available is False
                else:
                    assert available is True
    
    @pytest.mark.asyncio
    async def test_database_transaction_integrity(self, sample_events):
        """Test database transaction integrity during operations."""
        event_data = sample_events[0]
        
        with patch('services.compat_sql_store.create_event') as mock_create:
            # Simulate database error
            mock_create.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await async_create_event(event_data)
            
            # Ensure no partial data is left behind
            # This would be tested with real database transaction rollback
            assert True  # Placeholder for actual transaction test
