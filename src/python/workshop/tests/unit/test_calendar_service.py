"""
Unit tests for the Calendar Service components.
"""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.calendar_service import CalendarServiceInterface


@pytest.mark.unit
class TestCalendarServiceInterface:
    """Test the CalendarServiceInterface abstract base class."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CalendarServiceInterface()
    
    def test_interface_methods_are_abstract(self):
        """Test that all interface methods are abstract."""
        abstract_methods = CalendarServiceInterface.__abstractmethods__
        expected_methods = {"get_events", "get_rooms", "check_room_availability", "schedule_event", "generate_synthetic_data"}
        assert abstract_methods == expected_methods


# Mock implementation for testing
class MockCalendarService(CalendarServiceInterface):
    """Mock implementation of CalendarServiceInterface for testing."""
    
    def __init__(self):
        self._events = []
        self._rooms = [
            {"id": "room1", "name": "Conference Room A", "capacity": 10},
            {"id": "room2", "name": "Conference Room B", "capacity": 6},
            {"id": "room3", "name": "Meeting Room C", "capacity": 4}
        ]
    
    async def get_events(self, start_date, end_date, room_id=None):
        """Mock get_events implementation."""
        filtered_events = self._events
        if room_id:
            filtered_events = [e for e in filtered_events if e.get("room_id") == room_id]
        return json.dumps({"events": filtered_events})
    
    async def get_rooms(self):
        """Mock get_rooms implementation."""
        return json.dumps({"rooms": self._rooms})
    
    async def check_room_availability(self, room_id, start_time, end_time):
        """Mock check_room_availability implementation."""
        # Simple mock logic - room is available if no overlapping events
        overlapping = any(
            event.get("room_id") == room_id and
            event.get("start_time") < end_time.isoformat() and
            event.get("end_time") > start_time.isoformat()
            for event in self._events
        )
        return json.dumps({"available": not overlapping})
    
    async def schedule_event(self, event_data):
        """Mock schedule_event implementation."""
        # Add event to internal storage
        event = dict(event_data)
        if "id" not in event:
            event["id"] = f"event-{len(self._events) + 1}"
        self._events.append(event)
        return json.dumps({"success": True, "event": event})
    
    async def generate_synthetic_data(self, num_rooms=10, num_events=50):
        """Mock generate_synthetic_data implementation."""
        # Mock implementation - just return the numbers
        return (num_rooms, num_events)


@pytest.mark.unit  
class TestMockCalendarService:
    """Test the MockCalendarService implementation."""
    
    @pytest.fixture
    def calendar_service(self):
        """Create MockCalendarService instance."""
        return MockCalendarService()
    
    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing."""
        return {
            "id": "event-123",
            "title": "Test Meeting",
            "description": "Test meeting description",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "room_id": "room1",
            "attendees": "user1@test.com,user2@test.com",
            "organizer": "organizer@test.com"
        }
    
    @pytest.mark.asyncio
    async def test_get_rooms_returns_json_string(self, calendar_service):
        """Test that get_rooms returns a JSON string."""
        result = await calendar_service.get_rooms()
        
        assert isinstance(result, str)
        
        # Parse JSON to verify structure
        data = json.loads(result)
        assert "rooms" in data
        assert len(data["rooms"]) == 3
        assert data["rooms"][0]["id"] == "room1"
        assert data["rooms"][0]["name"] == "Conference Room A"
    
    @pytest.mark.asyncio
    async def test_get_events_empty_result(self, calendar_service):
        """Test get_events returns empty result when no events."""
        start_date = datetime(2024, 12, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 2, tzinfo=timezone.utc)
        
        result = await calendar_service.get_events(start_date, end_date)
        
        assert isinstance(result, str)
        data = json.loads(result)
        assert "events" in data
        assert len(data["events"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_events_with_data(self, calendar_service, sample_event_data):
        """Test get_events returns events when data exists."""
        # Add event to mock service
        calendar_service._events.append(sample_event_data)
        
        start_date = datetime(2024, 12, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 2, tzinfo=timezone.utc)
        
        result = await calendar_service.get_events(start_date, end_date)
        
        data = json.loads(result)
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Test Meeting"
    
    @pytest.mark.asyncio
    async def test_get_events_filtered_by_room(self, calendar_service, sample_event_data):
        """Test get_events filters by room_id."""
        # Add events for different rooms
        event_room1 = sample_event_data.copy()
        event_room1["room_id"] = "room1"
        
        event_room2 = sample_event_data.copy()
        event_room2["id"] = "event-456"
        event_room2["room_id"] = "room2"
        event_room2["title"] = "Room 2 Meeting"
        
        calendar_service._events.extend([event_room1, event_room2])
        
        start_date = datetime(2024, 12, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 2, tzinfo=timezone.utc)
        
        # Get events for room1 only
        result = await calendar_service.get_events(start_date, end_date, room_id="room1")
        
        data = json.loads(result)
        assert len(data["events"]) == 1
        assert data["events"][0]["room_id"] == "room1"
        assert data["events"][0]["title"] == "Test Meeting"
    
    @pytest.mark.asyncio
    async def test_check_room_availability_available(self, calendar_service):
        """Test room availability when room is free."""
        start_time = datetime(2024, 12, 1, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 1, 11, 0, tzinfo=timezone.utc)
        
        result = await calendar_service.check_room_availability("room1", start_time, end_time)
        
        data = json.loads(result)
        assert data["available"] is True
    
    @pytest.mark.asyncio
    async def test_check_room_availability_conflict(self, calendar_service, sample_event_data):
        """Test room availability when room has conflict."""
        # Add conflicting event
        calendar_service._events.append(sample_event_data)
        
        # Try to book overlapping time
        start_time = datetime(2024, 12, 1, 10, 30, tzinfo=timezone.utc)  # Overlaps existing event
        end_time = datetime(2024, 12, 1, 11, 30, tzinfo=timezone.utc)
        
        result = await calendar_service.check_room_availability("room1", start_time, end_time)
        
        data = json.loads(result)
        assert data["available"] is False
    
    @pytest.mark.asyncio
    async def test_check_room_availability_no_conflict_different_room(self, calendar_service, sample_event_data):
        """Test room availability for different room has no conflict."""
        # Add event for room1
        calendar_service._events.append(sample_event_data)
        
        # Check availability for room2
        start_time = datetime(2024, 12, 1, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 1, 11, 0, tzinfo=timezone.utc)
        
        result = await calendar_service.check_room_availability("room2", start_time, end_time)
        
        data = json.loads(result)
        assert data["available"] is True
    
    def test_room_data_structure(self, calendar_service):
        """Test room data has expected structure."""
        rooms = calendar_service._rooms
        
        for room in rooms:
            assert "id" in room
            assert "name" in room
            assert "capacity" in room
            assert isinstance(room["capacity"], int)
    
    @pytest.mark.asyncio
    async def test_concurrent_availability_checks(self, calendar_service):
        """Test multiple concurrent availability checks."""
        import asyncio
        
        start_time = datetime(2024, 12, 1, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 1, 11, 0, tzinfo=timezone.utc)
        
        # Run multiple availability checks concurrently
        tasks = [
            calendar_service.check_room_availability(f"room{i}", start_time, end_time)
            for i in range(1, 4)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            data = json.loads(result)
            assert "available" in data
    
    @pytest.mark.asyncio
    async def test_get_events_with_room_filter(self):
        """Test get_events with room filter."""
        # This test would be for SyntheticCalendarService when implemented
        pass
    
    @pytest.mark.asyncio
    async def test_get_rooms_returns_json_string(self):
        """Test that get_rooms returns a JSON string."""
        # This test would be for SyntheticCalendarService when implemented
        pass
    
    @pytest.mark.asyncio
    async def test_check_room_availability_returns_json_string(self):
        """Test that check_room_availability returns a JSON string."""
        # This test would be for SyntheticCalendarService when implemented
        pass
