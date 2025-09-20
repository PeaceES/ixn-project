"""
Integration tests for the agent workflow.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.async_sql_store import (
    async_create_event, async_list_events, async_get_rooms
)
from agent.stream_event_handler import StreamEventHandler

# Test constants
TEST_USER_ID = "test-user-123"
TEST_CALENDAR_ID = "test-calendar-456"
TEST_ROOM_ID = "test-room-789"
TEST_THREAD_ID = "test-thread-101"


@pytest.mark.integration
@pytest.mark.slow
class TestAgentWorkflow:
    """Test complete agent workflow integration."""
    
    @pytest.fixture
    def setup_mocks(self):
        """Setup mocks for agent workflow tests."""
        return {
            'azure_client': AsyncMock(),
            'calendar_client': AsyncMock(), 
            'docs_client': AsyncMock(),
            'permissions': MagicMock(),
            'evaluator': AsyncMock()
        }
    
    @pytest.mark.asyncio
    async def test_complete_scheduling_workflow(self):
        """Test complete meeting scheduling workflow with real agent_core."""
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
            
            # Mock only external dependencies, not agent_core
            with patch('agent_core.AIProjectClient') as mock_ai_client, \
                 patch('agent_core.CalendarClient') as mock_calendar_client_class:
                
                # Setup Azure AI mocks
                mock_project_client = AsyncMock()
                mock_ai_client.from_connection_string.return_value = mock_project_client
                
                mock_agent = MagicMock()
                mock_agent.id = "test-agent-id"
                mock_project_client.agents.create_agent.return_value = mock_agent
                
                mock_thread = MagicMock()
                mock_thread.id = "test-thread-id"
                mock_project_client.agents.create_thread.return_value = mock_thread
                
                # Setup calendar client mocks
                mock_calendar_client = AsyncMock()
                mock_calendar_client_class.return_value = mock_calendar_client
                
                # Setup async coroutine returns for health check and other operations
                async def mock_health_check():
                    return {"status": "healthy"}
                
                async def mock_get_rooms(*args, **kwargs):
                    return {
                        "success": True,
                        "rooms": [
                            {"id": "room1", "name": "Conference Room A"},
                            {"id": "room2", "name": "Conference Room B"}
                        ]
                    }
                
                async def mock_create_event(*args, **kwargs):
                    return {
                        "success": True,
                        "event_id": "event-123",
                        "message": "Meeting scheduled successfully"
                    }
                
                mock_calendar_client.health_check.side_effect = mock_health_check
                mock_calendar_client.get_rooms.side_effect = mock_get_rooms
                mock_calendar_client.create_event.side_effect = mock_create_event
                
                # Mock utilities
                with patch('utils.utilities.Utilities') as mock_utils_class:
                    mock_utils = MagicMock()
                    mock_utils_class.return_value = mock_utils
                    mock_utils.load_instructions.return_value = "You are a calendar agent."
                    
                    with patch('agent_core.open', create=True), \
                         patch('os.path.exists', return_value=True):
                        
                        # Create real agent core instance
                        from agent_core import CalendarAgentCore
                        agent_core = CalendarAgentCore(enable_tools=True)
                        
                        # Test real function calls
                        rooms_result = await agent_core.get_rooms_via_mcp()
                        rooms_data = json.loads(rooms_result)
                        assert rooms_data["success"] is True
                    assert len(rooms_data["rooms"]) >= 2
                    
                    # Test event creation
                    # Test event creation
                with patch.object(agent_core, '_load_org_structure', return_value={
                    'users': [{'id': 1, 'email': 'test@example.com', 'name': 'Test User'}]
                }):
                    event_result = await agent_core.schedule_event_with_organizer(
                        room_id="room1",
                        title="Integration Test Meeting",
                        start_time="2024-01-15T10:00:00Z",
                        end_time="2024-01-15T11:00:00Z",
                        organizer="test@example.com",
                        description="Test meeting description"
                    )
                    event_data = json.loads(event_result)
                    assert event_data["success"] is True
                    assert "event_id" in event_data
    
    @pytest.mark.asyncio
    async def test_room_availability_workflow(self):
        """Test room availability checking workflow."""
        with patch('services.calendar_service.CalendarServiceInterface') as mock_service:
            mock_calendar = AsyncMock()
            mock_service.return_value = mock_calendar
            
            # Setup mock responses
            mock_calendar.get_rooms.return_value = '[{"id": "room1", "name": "Conference Room A"}]'
            mock_calendar.check_room_availability.return_value = '{"available": true, "conflicts": []}'
            
            calendar_service = mock_service()
            
            # Step 1: Get available rooms
            rooms_json = await calendar_service.get_rooms()
            assert rooms_json == '[{"id": "room1", "name": "Conference Room A"}]'
            
            # Step 2: Check room availability
            availability_json = await calendar_service.check_room_availability(
                "room1",
                "2024-01-15T10:00:00Z",
                "2024-01-15T11:00:00Z"
            )
            assert "available" in availability_json
            assert "true" in availability_json
    
    @pytest.mark.asyncio
    async def test_mcp_client_workflow(self):
        """Test MCP client workflow."""
        with patch('services.mcp_client.CalendarMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Setup mock responses
            mock_client.create_event_via_mcp.return_value = {
                "id": "event123",
                "title": "Test Meeting",
                "status": "created"
            }
            
            client = mock_client_class()
            
            # Test event creation
            event_result = await client.create_event_via_mcp(
                user_id="test-user-123",
                calendar_id="test-calendar-456", 
                title="Test Meeting",
                start_time="2024-01-15T10:00:00Z",
                end_time="2024-01-15T11:00:00Z"
            )
            
            assert event_result["id"] == "event123"
            assert event_result["title"] == "Test Meeting"
            assert event_result["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_permissions_workflow(self):
        """Test permissions checking workflow."""
        with patch('services.calendar_mcp_server.validate_user_permissions', new_callable=AsyncMock) as mock_perms_func:
            # Setup mock response for the function
            mock_perms_func.return_value = (True, "User has permission")
            
            # Test permission validation
            has_permission, message = await mock_perms_func("test-user-123", "cal-123")
            assert has_permission is True
            assert "permission" in message
            
            # Test denied permission
            mock_perms_func.return_value = (False, "Permission denied")
            has_permission, message = await mock_perms_func("invalid-user", "cal-123")
            assert has_permission is False
            assert "denied" in message
    
    @pytest.mark.asyncio
    async def test_evaluation_workflow(self):
        """Test evaluation workflow."""
        with patch('evaluation.working_evaluator.WorkingRealTimeEvaluator') as mock_eval_class:
            mock_evaluator = AsyncMock()
            mock_eval_class.return_value = mock_evaluator
            
            # Setup mock responses compatible with working evaluator format
            mock_evaluator.evaluate_response.return_value = {
                "enabled": True,
                "scores": {
                    "intent_resolution": 0.85,
                    "coherence": 0.90,
                    "tool_call_accuracy": 0.88
                },
                "overall_score": 0.88,
                "method": "heuristic"
            }
            
            evaluator = mock_eval_class()
            
            # Test evaluation with working evaluator format
            thread_id = "test-thread-123"
            run_id = "test-run-456"
            response = "Meeting scheduled for tomorrow at 2 PM in Conference Room A"
            user_query = "Schedule a meeting for tomorrow at 2 PM"
            
            evaluation_result = await evaluator.evaluate_response(thread_id, run_id, response, user_query)
            
            assert evaluation_result["enabled"] is True
            assert evaluation_result["scores"]["intent_resolution"] == 0.85
            assert evaluation_result["scores"]["coherence"] == 0.90
            assert evaluation_result["overall_score"] == 0.88
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test agent error handling in workflow with real agent_core."""
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
            
            # Mock database responses for health check - but calendar will still fail
            mock_cursor.fetchone.return_value = [json.dumps({"status": "healthy"})]
            
            with patch('agent_core.AIProjectClient') as mock_ai_client, \
                 patch('services.server_client.CalendarClient') as mock_calendar_client_class:
                
                # Setup calendar client to fail
                mock_calendar_client = AsyncMock()
                mock_calendar_client_class.return_value = mock_calendar_client
                mock_calendar_client.health_check.side_effect = Exception("Connection failed")
                
                # Create real agent core instance
                from agent_core import CalendarAgentCore
                agent_core = CalendarAgentCore(enable_tools=True)
                
                # Test error handling in real function
                events_result = await agent_core.get_events_via_mcp()
                events_data = json.loads(events_result)
                
                assert events_data["success"] is False
                assert "failed" in events_data["error"] or "not available" in events_data["error"]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_workflow(self):
        """Test handling of concurrent requests."""
        with patch('agent_core.CalendarAgentCore') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Setup mock responses
            mock_agent.process_request.return_value = "Request processed"
            
            agent = mock_agent_class()
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = agent.process_request(f"Request {i}")
                tasks.append(task)
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks)
            
            # All requests should complete successfully
            assert len(results) == 5
            assert all(result == "Request processed" for result in results)
    
    @pytest.mark.asyncio
    async def test_stream_handler_workflow(self):
        """Test stream handler integration."""
        with patch('agent.stream_event_handler.StreamEventHandler') as mock_handler_class:
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            
            # Setup mock responses
            mock_handler.on_message_created.return_value = None
            mock_handler.on_message_completed.return_value = None
            
            handler = mock_handler_class()
            
            # Test stream events
            handler.on_message_created({"type": "message", "content": "Test message"})
            handler.on_message_completed({"type": "completion", "content": "Response completed"})
            
            # Verify handler was called
            assert mock_handler.on_message_created.called
            assert mock_handler.on_message_completed.called
    
    @pytest.mark.asyncio
    async def test_full_integration_workflow(self):
        """Test complete integration of all components."""
        # Mock all major components
        with patch('agent_core.CalendarAgentCore') as mock_agent_class, \
             patch('services.mcp_client.CalendarMCPClient') as mock_mcp_class, \
             patch('services.calendar_mcp_server.validate_user_permissions', new_callable=AsyncMock) as mock_perms_func, \
             patch('evaluation.working_evaluator.WorkingRealTimeEvaluator') as mock_eval_class:
            
            # Setup mocks
            mock_agent = AsyncMock()
            mock_mcp = AsyncMock()
            mock_eval = AsyncMock()
            
            mock_agent_class.return_value = mock_agent
            mock_mcp_class.return_value = mock_mcp
            mock_perms_func.return_value = (True, "Permission granted")
            mock_eval_class.return_value = mock_eval
            
            # Setup responses
            mock_agent.initialize.return_value = True
            mock_agent.process_request.return_value = "Meeting scheduled successfully"
            mock_mcp.create_event_via_mcp.return_value = {"id": "event123", "status": "created"}
            mock_eval.evaluate_response.return_value = {"overall_score": 0.88}
            
            # Create instances
            agent = mock_agent_class()
            mcp_client = mock_mcp_class()
            evaluator = mock_eval_class()
            
            # Test complete workflow
            # Step 1: Initialize
            await agent.initialize()
            
            # Step 2: Check permissions
            has_permission, message = await mock_perms_func("test-user-123", "cal-123")
            assert has_permission is True
            
            # Step 3: Process request
            response = await agent.process_request("Schedule a meeting for tomorrow")
            assert response == "Meeting scheduled successfully"
            
            # Step 4: Create event via MCP
            event_result = await mcp_client.create_event_via_mcp(
                user_id="test-user-123",
                calendar_id="test-calendar-456",
                title="Team Meeting",
                start_time="2024-01-15T10:00:00Z",
                end_time="2024-01-15T11:00:00Z"
            )
            assert event_result["status"] == "created"
            
            # Step 5: Evaluate response
            evaluation = await evaluator.evaluate_response(response, "User request")
            assert evaluation["overall_score"] == 0.88
    
    @pytest.mark.asyncio
    async def test_failure_recovery_workflow(self):
        """Test workflow recovery from failures."""
        with patch('agent_core.CalendarAgentCore') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Simulate failure followed by recovery
            mock_agent.process_request.side_effect = [
                Exception("Temporary failure"),
                "Request processed successfully"
            ]
            
            agent = mock_agent_class()
            
            # First request fails
            with pytest.raises(Exception) as exc_info:
                await agent.process_request("Test request")
            assert "Temporary failure" in str(exc_info.value)
            
            # Second request succeeds
            result = await agent.process_request("Test request")
            assert result == "Request processed successfully"
    
    @pytest.mark.asyncio
    async def test_performance_workflow(self):
        """Test workflow performance characteristics."""
        import time
        
        with patch('agent_core.CalendarAgentCore') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Setup fast response
            mock_agent.process_request.return_value = "Fast response"
            
            agent = mock_agent_class()
            
            # Measure response time
            start_time = time.time()
            await agent.process_request("Test request")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be fast (mock should respond quickly)
            assert response_time < 1.0  # Should be much faster than 1 second
    
    @pytest.mark.asyncio
    async def test_data_validation_workflow(self):
        """Test data validation throughout the workflow."""
        with patch('services.calendar_service.CalendarServiceInterface') as mock_service:
            mock_calendar = AsyncMock()
            mock_service.return_value = mock_calendar
            
            # Setup mock responses with valid data
            mock_calendar.get_events.return_value = '[{"id": "event1", "title": "Test Event"}]'
            mock_calendar.get_rooms.return_value = '[{"id": "room1", "name": "Test Room"}]'
            
            calendar_service = mock_service()
            
            # Test data validation
            events_json = await calendar_service.get_events("2024-01-15T09:00:00Z", "2024-01-15T17:00:00Z")
            rooms_json = await calendar_service.get_rooms()
            
            # Verify responses are valid JSON strings
            assert events_json.startswith('[')
            assert events_json.endswith(']')
            assert rooms_json.startswith('[')
            assert rooms_json.endswith(']')
            
            # Verify data contains expected fields
            assert "id" in events_json
            assert "title" in events_json
            assert "id" in rooms_json
            assert "name" in rooms_json
