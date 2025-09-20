"""
Unit tests for agent_core.py methods and functionality.
These tests isolate specific methods while mocking dependencies.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_core import CalendarAgentCore


@pytest.mark.unit
class TestCalendarAgentCoreUnit:
    """Unit tests for CalendarAgentCore methods."""
    
    @pytest.fixture
    def agent_core(self):
        """Create agent_core instance with tools disabled for isolated testing."""
        return CalendarAgentCore(enable_tools=False)
    
    @pytest.fixture
    def agent_core_with_tools(self):
        """Create agent_core instance with tools enabled.""" 
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'ENABLED_FUNCTIONS': 'ALL',
        }.get(key, default)):
            return CalendarAgentCore(enable_tools=True)
    
    def test_init_with_tools_disabled(self):
        """Test agent_core initialization with tools disabled."""
        agent_core = CalendarAgentCore(enable_tools=False)
        
        assert agent_core._enable_tools is False
        assert agent_core._tools_initialized is False
        assert agent_core.functions is None
        assert agent_core.agent is None
        assert agent_core.thread is None
        assert not agent_core._operation_active
    
    def test_init_with_tools_enabled(self):
        """Test agent_core initialization with tools enabled."""
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'ENABLED_FUNCTIONS': 'ALL',
        }.get(key, default)):
            agent_core = CalendarAgentCore(enable_tools=True)
            
            assert agent_core._enable_tools is True
            assert agent_core._tools_initialized is True
            assert agent_core.functions is not None
    
    def test_init_with_user_context(self):
        """Test agent_core initialization with user context from environment."""
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'AGENT_USER_ID': 'test-user-123',
            'AGENT_USER_NAME': 'Test User',
            'AGENT_USER_EMAIL': 'test@example.com'
        }.get(key, default)):
            agent_core = CalendarAgentCore(enable_tools=False)
            
            assert agent_core.default_user_context is not None
            assert agent_core.default_user_context['id'] == 'test-user-123'
            assert agent_core.default_user_context['name'] == 'Test User' 
            assert agent_core.default_user_context['email'] == 'test@example.com'
    
    def test_cleanup_run_thread(self, agent_core):
        """Test the cleanup method resets state properly."""
        # Set some state
        agent_core.agent = MagicMock()
        agent_core.thread = MagicMock()
        agent_core.shared_thread_id = "test-123"
        agent_core._operation_active = True
        
        # Call cleanup
        agent_core._cleanup_run_thread()
        
        # Verify state reset
        assert agent_core.agent is None
        assert agent_core.thread is None
        assert agent_core.shared_thread_id is None
        assert not agent_core._operation_active
    
    @pytest.mark.asyncio
    async def test_get_events_via_mcp_success(self, agent_core_with_tools):
        """Test get_events_via_mcp with successful response."""
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            with patch.object(agent_core_with_tools.calendar_client, 'list_events', new_callable=AsyncMock) as mock_list:
                
                mock_health.return_value = {"status": "healthy"}
                mock_list.return_value = {
                    "success": True,
                    "events": [
                        {"id": "1", "title": "Meeting 1"},
                        {"id": "2", "title": "Meeting 2"}
                    ]
                }
                
                result = await agent_core_with_tools.get_events_via_mcp()
                result_data = json.loads(result)
                
                assert result_data["success"] is True
                assert len(result_data["events"]) == 2
                mock_health.assert_called_once()
                mock_list.assert_called_once_with("all")
    
    @pytest.mark.asyncio
    async def test_get_events_via_mcp_unhealthy_service(self, agent_core_with_tools):
        """Test get_events_via_mcp with unhealthy service."""
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            
            mock_health.return_value = {"status": "unhealthy"}
            
            result = await agent_core_with_tools.get_events_via_mcp()
            result_data = json.loads(result)
            
            assert result_data["success"] is False
            assert "not available" in result_data["error"]
            mock_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_via_mcp_exception(self, agent_core_with_tools):
        """Test get_events_via_mcp with exception handling."""
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            
            mock_health.side_effect = Exception("Connection failed")
            
            result = await agent_core_with_tools.get_events_via_mcp()
            result_data = json.loads(result)
            
            assert result_data["success"] is False
            assert "failed" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_get_rooms_via_mcp_success(self, agent_core_with_tools):
        """Test get_rooms_via_mcp with successful response."""
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            with patch.object(agent_core_with_tools.calendar_client, 'get_rooms', new_callable=AsyncMock) as mock_rooms:
                
                mock_health.return_value = {"status": "healthy"}
                mock_rooms.return_value = {
                    "success": True,
                    "rooms": [
                        {"id": "room1", "name": "Conference A"},
                        {"id": "room2", "name": "Conference B"}
                    ]
                }
                
                result = await agent_core_with_tools.get_rooms_via_mcp()
                result_data = json.loads(result)
                
                assert result_data["success"] is True
                assert len(result_data["rooms"]) == 2
                mock_health.assert_called_once()
                mock_rooms.assert_called_once()
    
    @pytest.mark.asyncio  
    async def test_check_room_availability_via_mcp_success(self, agent_core_with_tools):
        """Test check_room_availability_via_mcp with successful response."""
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            with patch.object(agent_core_with_tools.calendar_client, 'check_room_availability', new_callable=AsyncMock) as mock_check:
                
                mock_health.return_value = {"status": "healthy"}
                mock_check.return_value = {
                    "success": True,
                    "available": True,
                    "conflicts": []
                }
                
                result = await agent_core_with_tools.check_room_availability_via_mcp(
                    room_id="room1",
                    start_time="2024-12-01T10:00:00Z",
                    end_time="2024-12-01T11:00:00Z"
                )
                result_data = json.loads(result)
                
                assert result_data["success"] is True
                assert result_data["available"] is True
                mock_health.assert_called_once()
                mock_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_event_with_organizer_success(self, agent_core_with_tools):
        """Test schedule_event_with_organizer with successful response."""
        # Mock the _load_org_structure method to return proper dict format
        with patch.object(agent_core_with_tools, '_load_org_structure', return_value={
            'users': [{'id': 1, 'email': 'organizer@test.com', 'name': 'Test Organizer'}]
        }):
            with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
                with patch.object(agent_core_with_tools.calendar_client, 'create_event', new_callable=AsyncMock) as mock_create:
                    
                    mock_health.return_value = {"status": "healthy"}
                    mock_create.return_value = {
                        "success": True,
                        "event_id": "new-event-123",
                        "message": "Event created successfully"
                    }
                    
                    result = await agent_core_with_tools.schedule_event_with_organizer(
                        room_id="test-room-1",
                        title="Unit Test Meeting",
                        start_time="2024-12-01T14:00:00Z", 
                        end_time="2024-12-01T15:00:00Z",
                        organizer="organizer@test.com",
                        description="Test meeting description"
                    )
                    result_data = json.loads(result)
                    
                    # Debug: print the actual result to see what's happening
                    print(f"DEBUG: result = {result}")
                    print(f"DEBUG: result_data = {result_data}")
                    
                    assert result_data["success"] is True
                    assert result_data["event_id"] == "new-event-123"
                    mock_health.assert_called_once()
                    mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_event_missing_required_fields(self, agent_core_with_tools):
        """Test schedule_event_with_organizer with missing required fields."""
        # Mock the database connection using the same pattern that works for integration tests
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection for database operations
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up context manager behavior
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Mock database responses for health check
            mock_cursor.fetchone.return_value = [json.dumps({"status": "healthy"})]
            
            # Mock the _load_org_structure method to return proper dict format
            with patch.object(agent_core_with_tools, '_load_org_structure', return_value={
                'users': [{'id': 1, 'email': 'organizer@test.com', 'name': 'Test Organizer'}]
            }):
                result = await agent_core_with_tools.schedule_event_with_organizer(
                    room_id="test-room-1",
                    title="",  # Empty title
                    start_time="2024-12-01T14:00:00Z",
                    end_time="2024-12-01T15:00:00Z",
                    organizer="organizer@test.com"
                )
                result_data = json.loads(result)
                
                assert result_data["success"] is False
                assert "required" in result_data["error"].lower()
    
    def test_function_initialization_all_functions(self):
        """Test function initialization with ALL functions enabled."""
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'ENABLED_FUNCTIONS': 'ALL',
        }.get(key, default)):
            
            agent_core = CalendarAgentCore(enable_tools=True)
            
            assert agent_core._tools_initialized is True
            assert agent_core.functions is not None
    
    def test_function_initialization_subset(self):
        """Test function initialization with subset of functions."""
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'ENABLED_FUNCTIONS': 'get_events_via_mcp,get_rooms_via_mcp',
        }.get(key, default)):
            
            agent_core = CalendarAgentCore(enable_tools=True)
            
            assert agent_core._tools_initialized is True 
            assert agent_core.functions is not None
    
    def test_function_initialization_invalid_function(self):
        """Test function initialization with invalid function name."""
        with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
            'ENABLED_FUNCTIONS': 'invalid_function_name',
        }.get(key, default)):
            
            # Should still initialize with default ALL functions
            agent_core = CalendarAgentCore(enable_tools=True)
            
            assert agent_core._tools_initialized is True
            assert agent_core.functions is not None
    
    @pytest.mark.asyncio
    async def test_process_message_not_initialized(self, agent_core):
        """Test process_message when agent is not initialized."""
        success, response = await agent_core.process_message("Hello")
        
        assert success is False
        assert "not initialized" in response
    
    @pytest.mark.asyncio
    async def test_process_message_busy(self, agent_core):
        """Test process_message when agent is busy."""
        agent_core.agent = MagicMock()
        agent_core.thread = MagicMock()
        agent_core._operation_active = True
        
        success, response = await agent_core.process_message("Hello")
        
        assert success is False
        assert "busy" in response
    
    @pytest.mark.asyncio
    async def test_reschedule_event_missing_user_id(self, agent_core_with_tools):
        """Test reschedule_event_via_mcp without user ID."""
        result = await agent_core_with_tools.reschedule_event_via_mcp(
            event_id="event-123",
            new_start_time="2024-12-01T14:00:00Z",
            new_end_time="2024-12-01T15:00:00Z"
        )
        result_data = json.loads(result)
        
        assert result_data["success"] is False
        assert "identification required" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_reschedule_event_with_user_context(self, agent_core_with_tools):
        """Test reschedule_event_via_mcp with user context."""
        agent_core_with_tools.default_user_context = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            with patch.object(agent_core_with_tools.calendar_client, 'find_event_calendar', new_callable=AsyncMock) as mock_find:
                with patch.object(agent_core_with_tools.calendar_client, 'update_event', new_callable=AsyncMock) as mock_update:
                    
                    mock_health.return_value = {"status": "healthy"}
                    mock_find.return_value = {"success": True, "calendar_id": "cal-123"}
                    mock_update.return_value = {"success": True, "message": "Event rescheduled"}
                    
                    result = await agent_core_with_tools.reschedule_event_via_mcp(
                        event_id="event-123",
                        new_start_time="2024-12-01T14:00:00Z", 
                        new_end_time="2024-12-01T15:00:00Z"
                    )
                    result_data = json.loads(result)
                    
                    assert result_data["success"] is True
                    mock_health.assert_called_once()
                    mock_find.assert_called_once_with("event-123")
                    mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_modify_event_via_mcp_success(self, agent_core_with_tools):
        """Test modify_event_via_mcp with successful response.""" 
        agent_core_with_tools.default_user_context = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        
        with patch.object(agent_core_with_tools.calendar_client, 'health_check', new_callable=AsyncMock) as mock_health:
            with patch.object(agent_core_with_tools.calendar_client, 'find_event_calendar', new_callable=AsyncMock) as mock_find:
                with patch.object(agent_core_with_tools.calendar_client, 'update_event', new_callable=AsyncMock) as mock_update:
                    
                    mock_health.return_value = {"status": "healthy"}
                    mock_find.return_value = {"success": True, "calendar_id": "cal-123"}
                    mock_update.return_value = {"success": True, "message": "Event modified"}
                    
                    result = await agent_core_with_tools.modify_event_via_mcp(
                        event_id="event-123",
                        title="Modified Title",
                        location="New Location"
                    )
                    result_data = json.loads(result)
                    
                    assert result_data["success"] is True
                    mock_health.assert_called_once()
                    mock_find.assert_called_once()
                    mock_update.assert_called_once()
    
    def test_destructor_cleanup(self):
        """Test that destructor properly handles cleanup."""
        agent_core = CalendarAgentCore(enable_tools=False)
        
        # Set up calendar client mock
        mock_client = MagicMock()
        agent_core.calendar_client = mock_client
        
        # This should not raise any exceptions
        del agent_core
    
    @pytest.mark.asyncio
    async def test_org_structure_fetch(self, agent_core_with_tools):
        """Test org structure fetching functionality."""
        # Mock the database connection to avoid real database queries
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up context manager behavior
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Mock database responses for health check
            mock_cursor.fetchone.return_value = [json.dumps({"status": "healthy"})]
            
            # Mock the correct method that _async_fetch_org_structure actually calls
            with patch.object(agent_core_with_tools, 'fetch_org_structure') as mock_fetch_org:
                mock_fetch_org.return_value = {
                    "user1@test.com": {"id": "user1", "email": "user1@test.com", "name": "User One"},
                    "user2@test.com": {"id": "user2", "email": "user2@test.com", "name": "User Two"}
                }
                
                result = await agent_core_with_tools._async_fetch_org_structure()
                result_data = json.loads(result)
                
                assert "users" in result_data
                assert len(result_data["users"]) == 2
                mock_fetch_org.assert_called_once()
    
    def test_user_details_fetch(self, agent_core_with_tools):
        """Test user details fetching functionality."""
        # Mock the database connection using the same pattern that works for other tests
        with patch('services.compat_sql_store._conn') as mock_conn:
            # Setup mock cursor and connection for database operations
            mock_cursor = MagicMock()
            mock_connection = MagicMock()
            
            # Set up context manager behavior
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.cursor.return_value.__exit__.return_value = None
            
            # Mock the database to return user data as JSON string (as expected by get_user_by_id_or_email)
            user_data = {
                "id": "user-123",
                "email": "test@example.com", 
                "name": "Test User",
                "department": "Engineering"
            }
            mock_cursor.fetchone.return_value = [json.dumps(user_data)]
            
            # Mock the _load_org_structure method to return proper dict format
            with patch.object(agent_core_with_tools, '_load_org_structure', return_value={
                'users': [user_data]
            }):
                result = agent_core_with_tools.get_user_details("test@example.com")
                result_data = json.loads(result)
                
                # The method returns the user data wrapped in a success response
                assert result_data["success"] is True
                assert result_data["user"]["id"] == "user-123"
                assert result_data["user"]["email"] == "test@example.com"
