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
from services.synthetic_calendar_service import SyntheticCalendarService
from tests.test_framework import (
    AsyncTestCase, MockResponseBuilder, TestDataFactory, AssertionHelpers
)


class TestCalendarServiceInterface:
    """Test the CalendarServiceInterface abstract base class."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CalendarServiceInterface()
    
    def test_interface_methods_are_abstract(self):
        """Test that all interface methods are abstract."""
        abstract_methods = CalendarServiceInterface.__abstractmethods__
        expected_methods = {"get_events", "get_rooms", "check_room_availability"}
        assert abstract_methods == expected_methods


@pytest.mark.unit
class TestSyntheticCalendarService(AsyncTestCase):
    """Test the SyntheticCalendarService implementation."""
    
    def setup_mocks(self):
        """Setup mocks for synthetic calendar service tests."""
        self.service = SyntheticCalendarService()
    
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    @pytest.mark.asyncio
    async def test_get_events_returns_json_string(self):
        """Test that get_events returns a JSON string."""
        start_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
        
        result = await self.service.get_events(start_date, end_date)
        
        # Should return a JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        events = json.loads(result)
        assert isinstance(events, list)
        
        # Verify event structure
        for event in events:
            AssertionHelpers.assert_event_structure(event)
    
    @pytest.mark.asyncio
    async def test_get_events_with_room_filter(self):
        """Test get_events with room filter."""
        start_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
        room_id = "room_1"
        
        result = await self.service.get_events(start_date, end_date, room_id)
        
        assert isinstance(result, str)
        events = json.loads(result)
        assert isinstance(events, list)
        
        # All events should be for the specified room
        for event in events:
            if 'room_id' in event:
                assert event['room_id'] == room_id
    
    @pytest.mark.asyncio
    async def test_get_rooms_returns_json_string(self):
        """Test that get_rooms returns a JSON string."""
        result = await self.service.get_rooms()
        
        # Should return a JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        rooms = json.loads(result)
        assert isinstance(rooms, list)
        assert len(rooms) > 0
        
        # Verify room structure
        for room in rooms:
            AssertionHelpers.assert_room_structure(room)
    
    @pytest.mark.asyncio
    async def test_check_room_availability_returns_json_string(self):
        """Test that check_room_availability returns a JSON string."""
        room_id = "room_1"
        start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        
        result = await self.service.check_room_availability(room_id, start_time, end_time)
        
        # Should return a JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        availability = json.loads(result)
        assert isinstance(availability, dict)
        
        # Verify availability structure
        AssertionHelpers.assert_availability_structure(availability)
        assert availability['room_id'] == room_id
    
    @pytest.mark.asyncio
    async def test_check_room_availability_available_room(self):
        """Test checking availability for an available room."""
        room_id = "room_1"
        start_time = datetime(2024, 1, 15, 2, 0, 0, tzinfo=timezone.utc)  # Very early time
        end_time = datetime(2024, 1, 15, 3, 0, 0, tzinfo=timezone.utc)
        
        result = await self.service.check_room_availability(room_id, start_time, end_time)
        availability = json.loads(result)
        
        # Should be available at unusual hours
        assert availability['available'] is True
        assert len(availability.get('conflicts', [])) == 0
    
    @pytest.mark.asyncio
    async def test_check_room_availability_busy_room(self):
        """Test checking availability for a busy room during business hours."""
        room_id = "room_1"
        start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)  # Business hours
        end_time = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        
        result = await self.service.check_room_availability(room_id, start_time, end_time)
        availability = json.loads(result)
        
        # Should have room_id and available status
        assert availability['room_id'] == room_id
        assert 'available' in availability
        assert isinstance(availability['available'], bool)
    
    @pytest.mark.asyncio
    async def test_get_events_date_range_validation(self):
        """Test that get_events handles date range properly."""
        start_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 16, 17, 0, 0, tzinfo=timezone.utc)  # Next day
        
        result = await self.service.get_events(start_date, end_date)
        events = json.loads(result)
        
        # Should return events (synthetic service generates them)
        assert isinstance(events, list)
        
        # All events should be within the date range
        for event in events:
            if 'start' in event:
                event_start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                assert start_date <= event_start <= end_date
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self):
        """Test that service methods handle errors gracefully."""
        # Test with invalid room_id
        result = await self.service.check_room_availability("invalid_room", 
                                                           datetime.now(timezone.utc), 
                                                           datetime.now(timezone.utc))
        
        # Should still return valid JSON
        assert isinstance(result, str)
        availability = json.loads(result)
        assert isinstance(availability, dict)
        assert 'room_id' in availability
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test that the service handles concurrent requests."""
        import asyncio
        
        # Make multiple concurrent requests
        tasks = []
        for i in range(5):
            start_date = datetime(2024, 1, 15, 9 + i, 0, 0, tzinfo=timezone.utc)
            end_date = datetime(2024, 1, 15, 10 + i, 0, 0, tzinfo=timezone.utc)
            task = self.service.get_events(start_date, end_date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All requests should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, str)
            events = json.loads(result)
            assert isinstance(events, list)


@pytest.mark.unit
class TestCalendarServiceDataValidation:
    """Test data validation for calendar service methods."""
    
    def test_event_data_structure(self):
        """Test that event data has the correct structure."""
        event_data = TestDataFactory.create_event_data(1)[0]
        AssertionHelpers.assert_event_structure(event_data)
    
    def test_room_data_structure(self):
        """Test that room data has the correct structure."""
        room_data = TestDataFactory.create_room_data(1)[0]
        AssertionHelpers.assert_room_structure(room_data)
    
    def test_availability_data_structure(self):
        """Test that availability data has the correct structure."""
        availability_data = MockResponseBuilder.create_availability_response(
            "room_1", True, []
        )
        AssertionHelpers.assert_availability_structure(availability_data)
    
    def test_error_response_structure(self):
        """Test that error responses have the correct structure."""
        error_response = MockResponseBuilder.create_error_response(
            "ROOM_NOT_FOUND", "The specified room was not found"
        )
        
        assert 'error' in error_response
        assert 'code' in error_response['error']
        assert 'message' in error_response['error']
        assert error_response['error']['code'] == "ROOM_NOT_FOUND"
        assert error_response['error']['message'] == "The specified room was not found"


@pytest.mark.integration
class TestCalendarServiceIntegration:
    """Integration tests for calendar service components."""
    
    @pytest.mark.asyncio
    async def test_full_calendar_workflow(self):
        """Test a complete calendar workflow."""
        service = SyntheticCalendarService()
        
        # Step 1: Get available rooms
        rooms_result = await service.get_rooms()
        rooms = json.loads(rooms_result)
        assert len(rooms) > 0
        
        # Step 2: Check availability for first room
        room_id = rooms[0]['id']
        start_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
        
        availability_result = await service.check_room_availability(room_id, start_time, end_time)
        availability = json.loads(availability_result)
        
        assert availability['room_id'] == room_id
        assert 'available' in availability
        
        # Step 3: Get events for the same time period
        events_result = await service.get_events(start_time, end_time, room_id)
        events = json.loads(events_result)
        
        assert isinstance(events, list)
        
        # If room is not available, there should be conflicting events
        if not availability['available']:
            assert len(events) > 0 or len(availability.get('conflicts', [])) > 0
