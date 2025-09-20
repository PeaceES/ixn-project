"""
Unit tests for SQL Store components.
"""
import pytest
import json
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.async_sql_store import (
    async_get_rooms, async_list_events, async_create_event, 
    async_update_event, async_cancel_event, async_check_availability,
    async_get_all_events
)
from services.compat_sql_store import (
    get_rooms, list_events, create_event, update_event, 
    cancel_event, check_availability
)


@pytest.mark.unit
class TestAsyncSQLStore:
    """Test the async SQL store wrapper functions."""
    
    def setup_db_mock(self, mock_conn, return_value, is_json=True):
        """Helper method to setup database connection mock."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        
        # Set up the context manager properly
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        
        mock_conn.return_value = mock_connection
        
        # Set up the return value
        if is_json:
            mock_cursor.fetchone.return_value = (json.dumps(return_value) if return_value else None,)
        else:
            mock_cursor.fetchone.return_value = (return_value,)
        
        return mock_cursor, mock_connection
    
    @pytest.mark.asyncio
    async def test_async_get_rooms(self):
        """Test async wrapper for get_rooms."""
        expected_rooms = {"rooms": [{"id": "room1", "name": "Conference Room A"}]}
        expected_data = [{"id": "room1", "name": "Conference Room A"}]
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_data, is_json=True)
            result = await async_get_rooms()
            assert result == expected_rooms
    
    @pytest.mark.asyncio
    async def test_async_list_events(self):
        """Test async wrapper for list_events."""
        calendar_id = "room1"
        expected_events = {"events": [{"id": "event1", "title": "Test Meeting"}]}
        expected_data = [{"id": "event1", "title": "Test Meeting"}]
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_data, is_json=True)
            result = await async_list_events(calendar_id)
            assert result == expected_events
    
    @pytest.mark.asyncio
    async def test_async_create_event(self, sample_events):
        """Test async wrapper for create_event."""
        event_data = sample_events[0].copy()
        # Add required calendar_id field
        event_data["calendar_id"] = "room1"
        expected_result = {"success": True, "event_id": "new-event-123"}
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = await async_create_event(event_data)
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_async_update_event(self):
        """Test async wrapper for update_event."""
        event_id = "event-123"
        patch_data = {"title": "Updated Meeting"}
        requester_email = "user@test.com"
        expected_result = {"success": True}
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = await async_update_event(event_id, patch_data, requester_email)
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_async_cancel_event(self):
        """Test async wrapper for cancel_event."""
        event_id = "event-123"
        requester_email = "user@test.com"
        expected_result = {"success": True}
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = await async_cancel_event(event_id, requester_email)
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_async_check_availability(self):
        """Test async wrapper for check_availability."""
        calendar_id = "room1"
        start_iso = "2024-12-01T09:00:00Z"
        end_iso = "2024-12-01T10:00:00Z"
        expected_result = True
        
        # Mock the database connection properly
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=False)
            result = await async_check_availability(calendar_id, start_iso, end_iso)
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_async_get_all_events(self):
        """Test getting all events from all rooms."""
        rooms_data = {"rooms": [{"id": "room1"}, {"id": "room2"}]}
        room1_events = {"events": [{"id": "event1", "title": "Meeting 1"}]}
        room2_events = {"events": [{"id": "event2", "title": "Meeting 2"}]}
        
        with patch('services.async_sql_store.async_get_rooms', return_value=rooms_data), \
             patch('services.async_sql_store.async_list_events', side_effect=[room1_events, room2_events]):
            
            result = await async_get_all_events()
            
            assert "events" in result
            assert len(result["events"]) == 2
            assert result["events"][0]["title"] == "Meeting 1"
            assert result["events"][1]["title"] == "Meeting 2"


@pytest.mark.unit
class TestCompatSQLStore:
    """Test the compatibility SQL store functions."""
    
    def setup_db_mock(self, mock_conn, return_value, is_json=True):
        """Helper method to setup database connection mock."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        
        # Set up the context manager properly
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        
        mock_conn.return_value = mock_connection
        
        # Set up the return value
        if is_json:
            mock_cursor.fetchone.return_value = (json.dumps(return_value) if return_value else None,)
        else:
            mock_cursor.fetchone.return_value = (return_value,)
        
        return mock_cursor, mock_connection
    
    def test_get_rooms_structure(self):
        """Test that get_rooms returns expected structure."""
        expected_data = []
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_data, is_json=True)
            result = get_rooms()
            assert isinstance(result, dict)
            assert "rooms" in result
    
    def test_list_events_structure(self):
        """Test that list_events returns expected structure."""
        expected_data = []
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_data, is_json=True)
            result = list_events("room1")
            assert isinstance(result, dict)
            assert "events" in result
    
    def test_create_event_validation(self, sample_events):
        """Test event creation with valid data."""
        event_data = sample_events[0].copy()
        # Add required calendar_id field
        event_data["calendar_id"] = "room1"
        expected_result = {"success": True, "event_id": "new-123"}
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = create_event(event_data)
            assert result["success"] is True
            assert "event_id" in result
    
    def test_update_event_permissions(self):
        """Test event update requires proper permissions."""
        event_id = "event-123"
        patch_data = {"title": "Updated Title"}
        requester_email = "unauthorized@test.com"
        expected_result = {"success": False, "error": "Unauthorized"}
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = update_event(event_id, patch_data, requester_email)
            assert result["success"] is False
            assert "error" in result
    
    def test_check_availability_conflict(self):
        """Test availability check detects conflicts."""
        calendar_id = "room1"
        start_iso = "2024-12-01T09:00:00Z"
        end_iso = "2024-12-01T10:00:00Z"
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, False, is_json=False)  # Room is not available
            result = check_availability(calendar_id, start_iso, end_iso)
            assert result is False
    
    def test_cancel_event_permissions(self):
        """Test event cancellation requires proper permissions."""
        event_id = "event-123"
        requester_email = "unauthorized@test.com"
        expected_result = {"success": False, "error": "Unauthorized"}
        
        with patch('services.compat_sql_store._conn') as mock_conn:
            self.setup_db_mock(mock_conn, expected_result, is_json=True)
            result = cancel_event(event_id, requester_email)
            assert result["success"] is False
            assert "error" in result
