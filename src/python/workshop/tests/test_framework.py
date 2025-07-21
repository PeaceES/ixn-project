"""
Test framework utilities and base classes for the Calendar Scheduler Agent tests.
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


class BaseTestCase(ABC):
    """Base class for test cases with common setup and utilities."""
    
    def setup_method(self):
        """Setup method called before each test method."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_mocks()
    
    def teardown_method(self):
        """Teardown method called after each test method."""
        self.cleanup_mocks()
    
    @abstractmethod
    def setup_mocks(self):
        """Setup mocks specific to the test class."""
        pass
    
    @abstractmethod
    def cleanup_mocks(self):
        """Cleanup mocks specific to the test class."""
        pass


class AsyncTestCase(BaseTestCase):
    """Base class for async test cases."""
    
    def setup_method(self):
        """Setup for async tests."""
        super().setup_method()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def teardown_method(self):
        """Teardown for async tests."""
        super().teardown_method()
        self.loop.close()


class MockResponseBuilder:
    """Builder class for creating consistent mock responses."""
    
    @staticmethod
    def create_calendar_event_response(event_id: str, title: str, start_time: str, end_time: str, 
                                     location: str = "", description: str = "") -> Dict[str, Any]:
        """Create a mock calendar event response."""
        return {
            "id": event_id,
            "title": title,
            "start": start_time,
            "end": end_time,
            "location": location,
            "description": description,
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
            "status": "confirmed"
        }
    
    @staticmethod
    def create_room_response(room_id: str, name: str, capacity: int, 
                           equipment: List[str] = None) -> Dict[str, Any]:
        """Create a mock room response."""
        return {
            "id": room_id,
            "name": name,
            "capacity": capacity,
            "equipment": equipment or [],
            "available": True,
            "location": f"Building A, Floor 1, {name}"
        }
    
    @staticmethod
    def create_availability_response(room_id: str, available: bool, 
                                   conflicts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a mock availability response."""
        return {
            "room_id": room_id,
            "available": available,
            "conflicts": conflicts or [],
            "checked_at": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def create_error_response(error_code: str, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a mock error response."""
        return {
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            }
        }


class TestDataFactory:
    """Factory class for generating test data."""
    
    @staticmethod
    def create_event_data(count: int = 1, start_date: str = "2024-01-15", 
                         base_hour: int = 10) -> List[Dict[str, Any]]:
        """Generate test event data."""
        events = []
        for i in range(count):
            event = MockResponseBuilder.create_calendar_event_response(
                event_id=f"event_{i + 1}",
                title=f"Test Event {i + 1}",
                start_time=f"{start_date}T{base_hour + i:02d}:00:00Z",
                end_time=f"{start_date}T{base_hour + i + 1:02d}:00:00Z",
                location=f"Room {i + 1}",
                description=f"Test event number {i + 1}"
            )
            events.append(event)
        return events
    
    @staticmethod
    def create_room_data(count: int = 1) -> List[Dict[str, Any]]:
        """Generate test room data."""
        rooms = []
        for i in range(count):
            room = MockResponseBuilder.create_room_response(
                room_id=f"room_{i + 1}",
                name=f"Conference Room {chr(65 + i)}",  # A, B, C, etc.
                capacity=10 + i * 2,
                equipment=["projector", "whiteboard"] if i % 2 == 0 else ["tv", "conference_phone"]
            )
            rooms.append(room)
        return rooms


class AssertionHelpers:
    """Helper methods for common test assertions."""
    
    @staticmethod
    def assert_event_structure(event: Dict[str, Any]):
        """Assert that an event has the expected structure."""
        required_fields = ["id", "title", "start", "end"]
        for field in required_fields:
            assert field in event, f"Event missing required field: {field}"
        
        optional_fields = ["location", "description", "created", "updated", "status"]
        for field in optional_fields:
            if field in event:
                assert isinstance(event[field], str), f"Event field {field} should be string"
    
    @staticmethod
    def assert_room_structure(room: Dict[str, Any]):
        """Assert that a room has the expected structure."""
        required_fields = ["id", "name", "capacity"]
        for field in required_fields:
            assert field in room, f"Room missing required field: {field}"
        
        assert isinstance(room["capacity"], int), "Room capacity should be integer"
        assert room["capacity"] > 0, "Room capacity should be positive"
        
        if "equipment" in room:
            assert isinstance(room["equipment"], list), "Room equipment should be list"
    
    @staticmethod
    def assert_availability_structure(availability: Dict[str, Any]):
        """Assert that an availability response has the expected structure."""
        required_fields = ["room_id", "available"]
        for field in required_fields:
            assert field in availability, f"Availability missing required field: {field}"
        
        assert isinstance(availability["available"], bool), "Availability should be boolean"
        
        if "conflicts" in availability:
            assert isinstance(availability["conflicts"], list), "Conflicts should be list"


class MockContextManager:
    """Context manager for handling multiple mocks."""
    
    def __init__(self):
        self.mocks = []
        self.patches = []
    
    def add_mock(self, target: str, mock_obj: Any = None):
        """Add a mock to the context manager."""
        if mock_obj is None:
            mock_obj = MagicMock()
        patcher = patch(target, mock_obj)
        self.patches.append(patcher)
        return mock_obj
    
    def add_async_mock(self, target: str, mock_obj: Any = None):
        """Add an async mock to the context manager."""
        if mock_obj is None:
            mock_obj = AsyncMock()
        patcher = patch(target, mock_obj)
        self.patches.append(patcher)
        return mock_obj
    
    def __enter__(self):
        """Enter the context manager."""
        for patcher in self.patches:
            patcher.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        for patcher in self.patches:
            patcher.stop()


class AsyncTestRunner:
    """Utility class for running async tests."""
    
    @staticmethod
    def run_async_test(test_func, *args, **kwargs):
        """Run an async test function synchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_func(*args, **kwargs))
        finally:
            loop.close()


# Common test constants
TEST_USER_ID = "test_user_123"
TEST_CALENDAR_ID = "test_calendar_456"
TEST_ROOM_ID = "test_room_789"
TEST_EVENT_ID = "test_event_abc"
TEST_THREAD_ID = "test_thread_def"
TEST_AGENT_ID = "test_agent_ghi"

# Test date/time constants
TEST_START_DATE = "2024-01-15"
TEST_END_DATE = "2024-01-16"
TEST_START_TIME = "2024-01-15T10:00:00Z"
TEST_END_TIME = "2024-01-15T11:00:00Z"

# Test configuration
TEST_CONFIG = {
    "mcp_base_url": "http://localhost:8000",
    "timeout": 30.0,
    "max_retries": 3,
    "test_mode": True
}
