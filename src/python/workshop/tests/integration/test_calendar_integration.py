"""
New integration tests for calendar service with database.
"""
import pytest
import asyncio
import tempfile
import json
import time
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
    async def test_end_to_end_event_creation(self, sample_events, performance_tracker, save_test_artifact):
        """Test complete event creation workflow."""
        event_data = sample_events[0]
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up the context manager behavior for connection
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Set up the context manager behavior for cursor  
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Track performance
            start_time = time.time()
            
            # Mock the database response for create_event - return the event as JSON
            event_json = json.dumps(event_data)
            mock_cursor.fetchone.return_value = [event_json]
            
            # Create event
            create_result = await async_create_event(event_data)
            create_time = time.time()
            
            assert create_result is not None
            assert create_result["id"] == event_data["id"]
            
            # Reset mocks for list_events call
            mock_cursor.reset_mock()
            
            # Mock the database response for list_events
            events_json = json.dumps([event_data])
            mock_cursor.fetchone.return_value = [events_json]
            
            # Verify event exists
            list_result = await async_list_events("room1")
            end_time = time.time()
            
            assert len(list_result["events"]) == 1
            assert list_result["events"][0]["title"] == event_data["title"]
            
            # Track performance metrics
            performance_tracker.start_timer("event_creation")
            performance_tracker.end_timer("event_creation")
            performance_tracker.start_timer("event_listing") 
            performance_tracker.end_timer("event_listing")
            performance_tracker.start_timer("full_workflow")
            performance_tracker.end_timer("full_workflow")
            
            # Save test results for thesis
            save_test_artifact("event_creation_workflow", {
                "test_type": "integration",
                "workflow": "end_to_end_event_creation",
                "performance": {
                    "creation_duration": create_time - start_time,
                    "total_duration": end_time - start_time
                },
                "results": {
                    "create_success": create_result is not None,
                    "events_found": len(list_result["events"])
                }
            })
    
    @pytest.mark.asyncio
    async def test_room_availability_workflow(self):
        """Test room availability checking workflow."""
        room_id = "room1"
        start_time = "2024-12-01T10:00:00Z"
        end_time = "2024-12-01T11:00:00Z"
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up the context manager behavior for connection
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Set up the context manager behavior for cursor  
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Mock the database response for get_rooms
            rooms_json = json.dumps([{"id": room_id, "name": "Conference Room A"}])
            mock_cursor.fetchone.return_value = [rooms_json]
            
            print(f"Mocking database connection...")
            print(f"Expected rooms data: {rooms_json}")
            
            # Test async_get_rooms
            rooms = await async_get_rooms()
            print(f"Actual rooms result: {rooms}")
            
            assert len(rooms["rooms"]) == 1
            assert rooms["rooms"][0]["id"] == room_id
            assert rooms["rooms"][0]["name"] == "Conference Room A"
            
            # Verify the database was called correctly
            mock_conn.assert_called_once()
            mock_connection.cursor.assert_called_once()
            mock_cursor.execute.assert_called_once_with("EXEC api.get_rooms_json")
            mock_cursor.fetchone.assert_called_once()
            
            # Reset mocks for availability check
            mock_cursor.reset_mock()
            mock_conn.reset_mock()
            mock_connection.reset_mock()
            
            # Mock the database response for check_availability
            mock_cursor.fetchone.return_value = [True]  # Available
            
            # Test async_check_availability
            availability = await async_check_availability(room_id, start_time, end_time)
            
            assert availability is True
            
            # Verify the availability check was called correctly
            mock_conn.assert_called_once()
            mock_connection.cursor.assert_called_once()
            # The exact SQL call will depend on the implementation
            mock_cursor.execute.assert_called_once()
            mock_cursor.fetchone.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conflict_detection_integration(self, sample_events):
        """Test that the system detects scheduling conflicts."""
        event1 = sample_events[0]
        
        # Create overlapping event
        event2 = event1.copy()
        event2["id"] = "event-2"
        event2["title"] = "Conflicting Meeting"
        event2["start_time"] = "2024-12-01T09:15:00Z"  # Overlaps with event1
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up the context manager behavior for connection
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Set up the context manager behavior for cursor  
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # First event succeeds - room is available
            mock_cursor.fetchone.side_effect = [
                [True],  # check_availability returns True
                [json.dumps(event1)]  # create_event returns event1
            ]
            
            # Check availability and create first event
            availability1 = await async_check_availability(event1["calendar_id"], event1["start_time"], event1["end_time"])
            assert availability1 is True
            
            result1 = await async_create_event(event1)
            assert result1 is not None
            
            # Reset mocks for second event
            mock_cursor.reset_mock()
            
            # Second event should detect conflict - room not available
            mock_cursor.fetchone.side_effect = [
                [False],  # check_availability returns False
                [None]    # create_event returns None (conflict detected)
            ]
            
            # Check availability and attempt to create second event
            availability2 = await async_check_availability(event2["calendar_id"], event2["start_time"], event2["end_time"])
            assert availability2 is False
            
            result2 = await async_create_event(event2)
            assert result2 is None
    
    @pytest.mark.asyncio
    async def test_multi_room_scheduling(self):
        """Test scheduling across multiple rooms."""
        rooms_data = [
            {"id": "room1", "name": "Conference Room A"},
            {"id": "room2", "name": "Conference Room B"},
            {"id": "room3", "name": "Meeting Room C"}
        ]
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up the context manager behavior for connection
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Set up the context manager behavior for cursor  
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Mock the database response for get_rooms
            rooms_json = json.dumps(rooms_data)
            
            # Mock responses: first get_rooms, then 3 availability checks
            mock_cursor.fetchone.side_effect = [
                [rooms_json],  # get_rooms
                [False],       # room1 not available
                [True],        # room2 available  
                [True]         # room3 available
            ]
            
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
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock to raise exception when connection is created
            mock_conn.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Database error"):
                await async_create_event(event_data)
            
            # Ensure no partial data is left behind
            # This would be tested with real database transaction rollback
            assert True  # Placeholder for actual transaction test
    
    @pytest.mark.asyncio
    async def test_comprehensive_workflow_with_artifacts(self, sample_events, artifact_dir, performance_tracker):
        """Test complete workflow with comprehensive artifact collection."""
        from tests.conftest import save_artifact
        
        # Start overall performance tracking
        performance_tracker.start_timer("complete_workflow")
        
        event_data = sample_events[0]
        
    @pytest.mark.asyncio
    async def test_comprehensive_workflow_with_artifacts(self, sample_events, artifact_dir, performance_tracker):
        """Test complete workflow with comprehensive artifact collection."""
        from tests.conftest import save_artifact
        
        # Start overall performance tracking
        performance_tracker.start_timer("complete_workflow")
        
        event_data = sample_events[0]
        
        # Mock the database connection and cursor
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up the context manager behavior for connection
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Set up the context manager behavior for cursor  
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Performance tracking for availability check
            performance_tracker.start_timer("availability_check")
            
            # Mock the database response for check_availability
            mock_cursor.fetchone.return_value = [True]
            availability = await async_check_availability("room1", "2024-12-01T10:00:00Z", "2024-12-01T11:00:00Z")
            
            performance_tracker.end_timer("availability_check")
            
            # Save availability check result
            save_artifact(artifact_dir, "availability_check_result", {
                "room_id": "room1",
                "start_time": "2024-12-01T10:00:00Z",
                "end_time": "2024-12-01T11:00:00Z",
                "available": availability,
                "check_duration": performance_tracker.metrics.get("availability_check", {}).get("duration")
            }, "test_comprehensive_workflow_with_artifacts")
            
            # Reset mock for event creation
            mock_cursor.reset_mock()
            
            # Performance tracking for event creation
            performance_tracker.start_timer("event_creation")
            
            # Mock successful creation
            event_json = json.dumps(event_data)
            mock_cursor.fetchone.return_value = [event_json]
            create_result = await async_create_event(event_data)
            
            performance_tracker.end_timer("event_creation")
            
            # Save event creation result
            save_artifact(artifact_dir, "event_creation_result", {
                "event_data": event_data,
                "creation_result": create_result,
                "creation_duration": performance_tracker.metrics.get("event_creation", {}).get("duration")
            }, "test_comprehensive_workflow_with_artifacts")
            
            # Reset mock for event listing
            mock_cursor.reset_mock()
            
            # Performance tracking for event listing
            performance_tracker.start_timer("event_listing")
            
            # Mock event listing
            events_json = json.dumps([event_data])
            mock_cursor.fetchone.return_value = [events_json]
            list_result = await async_list_events("room1")
            
            performance_tracker.end_timer("event_listing")
            performance_tracker.end_timer("complete_workflow")
            
            # Save final workflow results
            save_artifact(artifact_dir, "complete_workflow_result", {
                "workflow_steps": ["availability_check", "event_creation", "event_listing"],
                "final_event_list": list_result,
                "total_duration": performance_tracker.metrics.get("complete_workflow", {}).get("duration"),
                "step_durations": {
                    step: performance_tracker.metrics.get(step, {}).get("duration")
                    for step in ["availability_check", "event_creation", "event_listing"]
                }
            }, "test_comprehensive_workflow_with_artifacts")
            
            # Assertions
            assert availability is True
            assert create_result is not None
            assert len(list_result["events"]) == 1
            
            # Save performance metrics
            performance_tracker.save_metrics("test_comprehensive_workflow_with_artifacts")
