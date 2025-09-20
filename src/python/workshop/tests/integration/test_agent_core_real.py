"""
True integration tests for agent_core.py that exercise real agent logic.
These tests mock only external dependencies while letting agent_core run naturally.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_core import CalendarAgentCore


@pytest.mark.integration
class TestAgentCoreRealIntegration:
    """Integration tests that exercise real agent_core logic."""
    
    @pytest.fixture
    def mock_azure_dependencies(self):
        """Mock only Azure AI dependencies, not agent_core itself."""
        mocks = {}
        
        # Mock Azure AI Project Client
        with patch('agent_core.AIProjectClient') as mock_ai_client:
            mock_project_client = AsyncMock()
            mock_ai_client.from_connection_string.return_value = mock_project_client
            
            # Mock agent creation
            mock_agent = MagicMock()
            mock_agent.id = "test-agent-id"
            mock_agent.name = "Test Calendar Agent"
            mock_project_client.agents.create_agent.return_value = mock_agent
            
            # Mock thread creation  
            mock_thread = MagicMock()
            mock_thread.id = "test-thread-id"
            mock_project_client.agents.create_thread.return_value = mock_thread
            
            # Mock message creation
            mock_project_client.agents.create_message.return_value = AsyncMock()
            
            # Mock run creation and completion
            mock_run = MagicMock()
            mock_run.id = "test-run-id"
            mock_run.status = "completed"
            mock_project_client.agents.create_run.return_value = mock_run
            mock_project_client.agents.get_run.return_value = mock_run
            
            # Mock run list
            mock_runs_paged = MagicMock()
            mock_runs_paged.data = [mock_run]
            mock_project_client.agents.list_runs.return_value = mock_runs_paged
            
            # Mock messages
            mock_message = MagicMock()
            mock_message.role = "assistant"
            mock_message.content = [MagicMock(text=MagicMock(value="Test response from agent"))]
            mock_messages_paged = MagicMock()
            mock_messages_paged.data = [mock_message]
            mock_project_client.agents.list_messages.return_value = mock_messages_paged
            
            # Mock auto function calls
            mock_project_client.agents.enable_auto_function_calls.return_value = AsyncMock()
            
            mocks['project_client'] = mock_project_client
            mocks['agent'] = mock_agent
            mocks['thread'] = mock_thread
            mocks['run'] = mock_run
            
            yield mocks
    
    @pytest.fixture  
    def mock_calendar_client(self):
        """Mock calendar client HTTP calls but let agent_core use it."""
        # Patch at the module level where agent_core imports it
        with patch('services.server_client.CalendarClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check
            mock_client.health_check.return_value = {"status": "healthy"}
            
            # Mock calendar operations
            mock_client.list_events.return_value = {
                "success": True,
                "events": [
                    {
                        "id": "event-1",
                        "title": "Team Meeting", 
                        "start_time": "2024-12-01T10:00:00Z",
                        "end_time": "2024-12-01T11:00:00Z"
                    }
                ]
            }
            
            mock_client.get_rooms.return_value = {
                "success": True,
                "rooms": [
                    {"id": "room-1", "name": "Conference Room A"},
                    {"id": "room-2", "name": "Conference Room B"}
                ]
            }
            
            mock_client.check_availability.return_value = {
                "success": True,
                "available": True,
                "conflicts": []
            }
            
            mock_client.create_event.return_value = {
                "success": True,
                "event_id": "new-event-123",
                "message": "Event created successfully"
            }
            
            # Mock close method for cleanup
            mock_client.close.return_value = AsyncMock()
            
            yield mock_client
    
    @pytest.fixture
    def mock_utilities(self):
        """Mock utilities but let agent_core use them."""
        with patch('utils.utilities.Utilities') as mock_utils_class:
            mock_utils = MagicMock()
            mock_utils_class.return_value = mock_utils
            
            # Mock instruction loading
            mock_utils.load_instructions.return_value = """
            You are a Calendar Scheduling Agent. Help users schedule meetings and manage their calendar.
            Available functions: get_events_via_mcp, get_rooms_via_mcp, schedule_event_with_organizer
            """
            
            yield mock_utils
    
    @pytest.mark.asyncio
    async def test_agent_initialization_workflow(self, mock_azure_dependencies, mock_calendar_client, mock_utilities):
        """Test that agent core properly initializes with real logic flow."""
        # Mock the database connection using the same pattern that works for unit tests
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
            
            # Create agent with tools enabled (real integration)
            agent_core = CalendarAgentCore(enable_tools=True)
        
        # Mock file operations for agent tools
        with patch('agent_core.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"fake font data"
            with patch('os.path.exists', return_value=True):
                with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
                    'ENABLED_FUNCTIONS': 'ALL',
                }.get(key, default)):
                    # Mock the PROJECT_CONNECTION_STRING directly since it's imported at module level
                    with patch('agent_core.PROJECT_CONNECTION_STRING', 'test.host;sub-id;rg;project'):
                    
                        # Test initialization
                        success, message = await agent_core.initialize_agent()
                        
                        # Print the actual message to see what's failing
                        print(f"DEBUG: success={success}, message='{message}'")
                        
                        assert success is True, f"Agent initialization failed: {message}"
                        assert "ready" in message.lower() or "initialized" in message.lower() or message == ""
                    
                    # Verify agent state
                    assert agent_core.agent is not None
                    assert agent_core.thread is not None
                    assert agent_core._tools_initialized is True
                    
                    # Verify Azure client interactions
                    mock_azure_dependencies['project_client'].agents.create_agent.assert_called_once()
                    # create_thread is called twice - once for regular thread, once for shared thread
                    assert mock_azure_dependencies['project_client'].agents.create_thread.call_count == 2
    
    @pytest.mark.asyncio
    async def test_message_processing_workflow(self, mock_azure_dependencies, mock_calendar_client, mock_utilities):
        """Test full message processing workflow with real agent_core logic."""
        agent_core = CalendarAgentCore(enable_tools=True)
        
        # Setup agent state
        agent_core.agent = mock_azure_dependencies['agent']
        agent_core.thread = mock_azure_dependencies['thread']
        agent_core.project_client = mock_azure_dependencies['project_client']
        agent_core._tools_initialized = True
        agent_core.functions = MagicMock()  # Mock the functions tool
        
        # Test message processing
        user_message = "What meetings do I have today?"
        success, response = await agent_core.process_message(user_message)
        
        assert success is True
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Verify the real message processing flow was executed
        mock_azure_dependencies['project_client'].agents.create_message.assert_called_once()
        mock_azure_dependencies['project_client'].agents.create_run.assert_called_once()
        mock_azure_dependencies['project_client'].agents.list_messages.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_calendar_function_execution(self, mock_azure_dependencies, mock_utilities):
        """Test that calendar functions are actually executed by agent_core."""
        # Mock the calendar client at import level BEFORE creating agent_core
        with patch('agent_core.CalendarClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check and list_events - return proper awaitable coroutines
            async def mock_health_check():
                return {"status": "healthy"}
            
            async def mock_list_events(*args, **kwargs):
                return {
                    "success": True,
                    "events": [
                        {
                            "id": "event-1",
                            "title": "Team Meeting", 
                            "start_time": "2024-12-01T10:00:00Z",
                            "end_time": "2024-12-01T11:00:00Z"
                        }
                    ]
                }
            
            mock_client.health_check.side_effect = mock_health_check
            mock_client.list_events.side_effect = mock_list_events
            
            # Now create agent_core (this will use our mocked CalendarClient)
            agent_core = CalendarAgentCore(enable_tools=True)
            
            # Test get_events_via_mcp function directly
            events_result = await agent_core.get_events_via_mcp()
            events_data = json.loads(events_result)
            
            assert events_data["success"] is True
            assert "events" in events_data
            assert len(events_data["events"]) >= 1
            
            # Verify calendar client was called
            mock_client.health_check.assert_called_once()
            mock_client.list_events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_room_availability_function(self, mock_azure_dependencies, mock_utilities):
        """Test room availability checking function execution."""
        # Mock the calendar client at import level BEFORE creating agent_core
        with patch('agent_core.CalendarClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check and room availability check - return proper awaitable coroutines
            async def mock_health_check():
                return {"status": "healthy"}
            
            async def mock_check_room_availability(*args, **kwargs):
                return {
                    "success": True,
                    "available": True,
                    "conflicts": []
                }
            
            mock_client.health_check.side_effect = mock_health_check
            mock_client.check_room_availability.side_effect = mock_check_room_availability
            
            # Now create agent_core (this will use our mocked CalendarClient)
            agent_core = CalendarAgentCore(enable_tools=True)
            
            # Test check_room_availability_via_mcp function
            availability_result = await agent_core.check_room_availability_via_mcp(
                room_id="room-1",
                start_time="2024-12-01T10:00:00Z", 
                end_time="2024-12-01T11:00:00Z"
            )
            availability_data = json.loads(availability_result)
            
            # Debug: print the actual result to see what's happening
            print(f"DEBUG: availability_result = {availability_result}")
            print(f"DEBUG: availability_data = {availability_data}")
            
            assert availability_data["success"] is True
            assert "available" in availability_data
            
            # Verify calendar client was called
            mock_client.health_check.assert_called_once()
            mock_client.check_room_availability.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_scheduling_function(self, mock_azure_dependencies, mock_calendar_client, mock_utilities):
        """Test event scheduling function execution.""" 
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
            
            # Mock database responses for health check
            mock_cursor.fetchone.return_value = [json.dumps({"status": "healthy"})]
            
            # Create agent with mocked calendar client
            with patch('agent_core.CalendarClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                
                # Setup async coroutine returns for health check and create_event
                async def mock_health_check():
                    return {"status": "healthy"}
                
                async def mock_create_event(*args, **kwargs):
                    return {"success": True, "event_id": "event-123"}
                
                mock_client.health_check.side_effect = mock_health_check
                mock_client.create_event.side_effect = mock_create_event
                
                agent_core = CalendarAgentCore(enable_tools=True)
                
                # Mock org structure loading
                with patch.object(agent_core, '_load_org_structure', return_value={
                    'users': [{'id': 1, 'email': 'test@example.com', 'name': 'Test User'}]
                }):
                    # Test schedule_event_with_organizer function with correct parameters
                    scheduling_result = await agent_core.schedule_event_with_organizer(
                        room_id="room-1",
                        title="Integration Test Meeting",
                        start_time="2024-12-01T14:00:00Z",
                        end_time="2024-12-01T15:00:00Z",
                        organizer="test@example.com",
                        description="Test meeting description"
                    )
                    scheduling_data = json.loads(scheduling_result)
                    
                    # Debug: print the actual result to see what's failing
                    print(f"DEBUG: scheduling_result = {scheduling_result}")
                    print(f"DEBUG: scheduling_data = {scheduling_data}")
                    
                    assert scheduling_data["success"] is True
                    assert "event_id" in scheduling_data
                    
                    # Verify calendar client was called
                    mock_client.health_check.assert_called_once()
                    mock_client.create_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_agent_core(self, mock_azure_dependencies, mock_utilities):
        """Test error handling paths in agent_core."""
        # Mock the calendar client at import level BEFORE creating agent_core
        with patch('agent_core.CalendarClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Test with unhealthy calendar service - return proper awaitable coroutine
            async def mock_unhealthy_check():
                return {"status": "unhealthy"}
            
            mock_client.health_check.side_effect = mock_unhealthy_check
            
            # Now create agent_core (this will use our mocked CalendarClient)
            agent_core = CalendarAgentCore(enable_tools=True)
            
            events_result = await agent_core.get_events_via_mcp()
            events_data = json.loads(events_result)
            
            assert events_data["success"] is False
            assert "not available" in events_data["error"]
            
            # Test with calendar client exception - return proper awaitable coroutine that raises
            async def mock_failing_check():
                raise Exception("Connection failed")
                
            mock_client.health_check.side_effect = mock_failing_check
            
            events_result = await agent_core.get_events_via_mcp()
            events_data = json.loads(events_result)
            
            assert events_data["success"] is False
            assert "connection failed" in events_data["error"].lower() or "mcp connection failed" in events_data["error"].lower() or "not available" in events_data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_prevention(self, mock_azure_dependencies, mock_calendar_client, mock_utilities):
        """Test that agent_core prevents concurrent operations."""
        agent_core = CalendarAgentCore(enable_tools=True)
        
        # Setup agent state
        agent_core.agent = mock_azure_dependencies['agent']
        agent_core.thread = mock_azure_dependencies['thread'] 
        agent_core.project_client = mock_azure_dependencies['project_client']
        agent_core._tools_initialized = True
        agent_core.functions = MagicMock()
        
        # Make first operation "slow"
        async def slow_create_run(*args, **kwargs):
            await asyncio.sleep(0.1)
            return mock_azure_dependencies['run']
            
        mock_azure_dependencies['project_client'].agents.create_run.side_effect = slow_create_run
        
        # Start first operation
        task1 = asyncio.create_task(agent_core.process_message("First message"))
        
        # Try second operation immediately  
        await asyncio.sleep(0.01)  # Let first operation start
        success2, response2 = await agent_core.process_message("Second message")
        
        # Second should be rejected due to busy state
        assert success2 is False
        assert "busy" in response2.lower()
        
        # First should complete successfully
        success1, response1 = await task1
        assert success1 is True
    
    @pytest.mark.asyncio
    async def test_function_initialization_control(self, mock_azure_dependencies, mock_utilities):
        """Test that function initialization respects ENABLED_FUNCTIONS setting."""
        # Mock the calendar client at import level BEFORE creating agent_core
        with patch('agent_core.CalendarClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check and operations - return proper awaitable coroutines
            async def mock_health_check():
                return {"status": "healthy"}
            
            async def mock_list_events(*args, **kwargs):
                return {"success": True, "events": []}
            
            async def mock_get_rooms(*args, **kwargs):
                return {"success": True, "rooms": []}
            
            mock_client.health_check.side_effect = mock_health_check
            mock_client.list_events.side_effect = mock_list_events
            mock_client.get_rooms.side_effect = mock_get_rooms
            
            with patch('agent_core.os.getenv', side_effect=lambda key, default=None: {
                'ENABLED_FUNCTIONS': 'get_events_via_mcp,get_rooms_via_mcp',
                'PROJECT_CONNECTION_STRING': 'test.host;sub-id;rg;project'
            }.get(key, default)):
                
                # Now create agent_core (this will use our mocked CalendarClient)
                agent_core = CalendarAgentCore(enable_tools=True)
                
                # Check that only specified functions were initialized
                assert agent_core._tools_initialized is True
                assert agent_core.functions is not None
                
                # Test that the limited functions work
                events_result = await agent_core.get_events_via_mcp()
                assert json.loads(events_result)["success"] is True
                
                rooms_result = await agent_core.get_rooms_via_mcp()
                assert json.loads(rooms_result)["success"] is True
    
    @pytest.mark.asyncio
    async def test_safe_mode_operation(self, mock_azure_dependencies, mock_utilities):
        """Test agent_core in safe mode (no tools)."""
        agent_core = CalendarAgentCore(enable_tools=False)
        
        # Verify tools are not initialized
        assert agent_core._enable_tools is False
        assert agent_core._tools_initialized is False
        assert agent_core.functions is None
        
        # Setup basic agent state for message processing
        agent_core.agent = mock_azure_dependencies['agent']
        agent_core.thread = mock_azure_dependencies['thread']
        agent_core.project_client = mock_azure_dependencies['project_client']
        
        # Test that message processing still works without tools
        success, response = await agent_core.process_message("Hello")
        assert success is True
        assert isinstance(response, str)
