"""
Unit tests for the MCP Client components.
"""
import pytest
import json
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mcp_client import CalendarMCPClient
from tests.test_framework import (
    AsyncTestCase, MockResponseBuilder, TestDataFactory, AssertionHelpers,
    TEST_USER_ID, TEST_CALENDAR_ID, TEST_ROOM_ID, TEST_EVENT_ID
)


@pytest.mark.unit
@pytest.mark.mcp
class TestCalendarMCPClient(AsyncTestCase):
    """Test the CalendarMCPClient class."""
    
    def setup_mocks(self):
        """Setup mocks for MCP client tests."""
        self.client = CalendarMCPClient("http://localhost:8000")
        self.mock_httpx_client = AsyncMock()
        self.mock_response = AsyncMock()
        
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with different base URLs."""
        # Test default URL
        client1 = CalendarMCPClient()
        assert client1.base_url == "http://localhost:8000"
        
        # Test custom URL
        client2 = CalendarMCPClient("https://api.example.com")
        assert client2.base_url == "https://api.example.com"
        
        # Test URL with trailing slash
        client3 = CalendarMCPClient("http://localhost:8000/")
        assert client3.base_url == "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_get_client_creates_httpx_client(self):
        """Test that _get_client creates and returns an httpx client."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance
            
            client = await self.client._get_client()
            
            assert client == mock_client_instance
            mock_client_class.assert_called_once_with(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
    
    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self):
        """Test that _get_client reuses existing client instance."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance
            
            # First call should create client
            client1 = await self.client._get_client()
            # Second call should reuse the same client
            client2 = await self.client._get_client()
            
            assert client1 == client2
            mock_client_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_closes_client(self):
        """Test that cleanup properly closes the httpx client."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance
            
            # Create client
            await self.client._get_client()
            
            # Cleanup should close the client
            await self.client.cleanup()
            
            mock_client_instance.aclose.assert_called_once()
            assert self.client._client is None
    
    @pytest.mark.asyncio
    async def test_cleanup_handles_close_error(self):
        """Test that cleanup handles errors when closing client."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.aclose.side_effect = Exception("Close error")
            mock_client_class.return_value = mock_client_instance
            
            # Create client
            await self.client._get_client()
            
            # Cleanup should handle the error gracefully
            await self.client.cleanup()
            
            assert self.client._client is None
    
    @pytest.mark.asyncio
    async def test_create_event_via_mcp_success(self):
        """Test successful event creation via MCP."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock()
            
            # Mock successful response
            event_data = MockResponseBuilder.create_calendar_event_response(
                TEST_EVENT_ID, "Test Meeting", "2024-01-15T10:00:00Z", "2024-01-15T11:00:00Z"
            )
            mock_response.json.return_value = event_data
            mock_response.status_code = 200
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance
            
            result = await self.client.create_event_via_mcp(
                user_id=TEST_USER_ID,
                calendar_id=TEST_CALENDAR_ID,
                title="Test Meeting",
                start_time="2024-01-15T10:00:00Z",
                end_time="2024-01-15T11:00:00Z",
                location="Conference Room A",
                description="Test meeting description"
            )
            
            # Verify the request was made correctly
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "http://localhost:8000/calendar/events"
            
            # Verify the payload
            payload = call_args[1]['json']
            assert payload['user_id'] == TEST_USER_ID
            assert payload['calendar_id'] == TEST_CALENDAR_ID
            assert payload['title'] == "Test Meeting"
            assert payload['start_time'] == "2024-01-15T10:00:00Z"
            assert payload['end_time'] == "2024-01-15T11:00:00Z"
            assert payload['location'] == "Conference Room A"
            assert payload['description'] == "Test meeting description"
            
            # Verify the result
            assert result == event_data
    
    @pytest.mark.asyncio
    async def test_create_event_via_mcp_http_error(self):
        """Test event creation with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock()
            
            # Mock HTTP error response
            mock_response.status_code = 400
            mock_response.json.return_value = MockResponseBuilder.create_error_response(
                "INVALID_REQUEST", "Invalid event data"
            )
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance
            
            with pytest.raises(Exception) as exc_info:
                await self.client.create_event_via_mcp(
                    user_id=TEST_USER_ID,
                    calendar_id=TEST_CALENDAR_ID,
                    title="Test Meeting",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z"
                )
            
            assert "Failed to create event" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_event_via_mcp_network_error(self):
        """Test event creation with network error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            
            # Mock network error
            mock_client_instance.post.side_effect = httpx.ConnectError("Connection failed")
            mock_client_class.return_value = mock_client_instance
            
            with pytest.raises(Exception) as exc_info:
                await self.client.create_event_via_mcp(
                    user_id=TEST_USER_ID,
                    calendar_id=TEST_CALENDAR_ID,
                    title="Test Meeting",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z"
                )
            
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_event_minimal_data(self):
        """Test creating event with minimal required data."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock()
            
            event_data = MockResponseBuilder.create_calendar_event_response(
                TEST_EVENT_ID, "Minimal Meeting", "2024-01-15T10:00:00Z", "2024-01-15T11:00:00Z"
            )
            mock_response.json.return_value = event_data
            mock_response.status_code = 200
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance
            
            result = await self.client.create_event_via_mcp(
                user_id=TEST_USER_ID,
                calendar_id=TEST_CALENDAR_ID,
                title="Minimal Meeting",
                start_time="2024-01-15T10:00:00Z",
                end_time="2024-01-15T11:00:00Z"
            )
            
            # Verify the request was made
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            payload = call_args[1]['json']
            
            # Verify required fields
            assert payload['user_id'] == TEST_USER_ID
            assert payload['calendar_id'] == TEST_CALENDAR_ID
            assert payload['title'] == "Minimal Meeting"
            
            # Verify optional fields are None
            assert payload['location'] is None
            assert payload['description'] is None
            
            assert result == event_data


@pytest.mark.integration
@pytest.mark.mcp
class TestMCPClientIntegration:
    """Integration tests for MCP client components."""
    
    @pytest.mark.asyncio
    async def test_calendar_mcp_client_full_lifecycle(self):
        """Test the full lifecycle of calendar MCP client."""
        client = CalendarMCPClient("http://localhost:8000")
        
        try:
            # Test client creation
            assert client.base_url == "http://localhost:8000"
            
            # Test client initialization (should not raise)
            await client._get_client()
            
            # Test cleanup
            await client.cleanup()
            
            # After cleanup, client should be None
            assert client._client is None
            
        except Exception as e:
            # If we can't connect to actual MCP server, that's expected in tests
            assert "Connection" in str(e) or "Network" in str(e)
    
    @pytest.mark.asyncio
    async def test_multiple_mcp_clients(self):
        """Test creating and managing multiple MCP clients."""
        client1 = CalendarMCPClient("http://localhost:8000")
        client2 = CalendarMCPClient("http://localhost:8001")
        
        try:
            # Both clients should be independently configurable
            assert client1.base_url == "http://localhost:8000"
            assert client2.base_url == "http://localhost:8001"
            
            # Both should be able to initialize
            await client1._get_client()
            await client2._get_client()
            
            # Both should be able to cleanup
            await client1.cleanup()
            await client2.cleanup()
            
        except Exception as e:
            # Expected in test environment without actual MCP servers
            assert "Connection" in str(e) or "Network" in str(e)


@pytest.mark.unit
@pytest.mark.mcp
class TestMCPClientErrorHandling:
    """Test error handling in MCP clients."""
    
    @pytest.mark.asyncio
    async def test_invalid_base_url(self):
        """Test handling of invalid base URLs."""
        client = CalendarMCPClient("invalid-url")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = httpx.InvalidURL("Invalid URL")
            mock_client_class.return_value = mock_client_instance
            
            with pytest.raises(Exception):
                await client.create_event_via_mcp(
                    user_id=TEST_USER_ID,
                    calendar_id=TEST_CALENDAR_ID,
                    title="Test",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z"
                )
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of request timeouts."""
        client = CalendarMCPClient("http://localhost:8000")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance
            
            with pytest.raises(Exception) as exc_info:
                await client.create_event_via_mcp(
                    user_id=TEST_USER_ID,
                    calendar_id=TEST_CALENDAR_ID,
                    title="Test",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z"
                )
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_json_parsing_error(self):
        """Test handling of JSON parsing errors."""
        client = CalendarMCPClient("http://localhost:8000")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock()
            
            # Mock response with invalid JSON
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance
            
            with pytest.raises(Exception):
                await client.create_event_via_mcp(
                    user_id=TEST_USER_ID,
                    calendar_id=TEST_CALENDAR_ID,
                    title="Test",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z"
                )
