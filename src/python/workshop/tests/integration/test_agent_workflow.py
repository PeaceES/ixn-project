"""
Integration tests for the agent workflow.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_framework import (
    AsyncTestCase, MockResponseBuilder, TestDataFactory, 
    TEST_USER_ID, TEST_CALENDAR_ID, TEST_ROOM_ID, TEST_THREAD_ID
)


@pytest.mark.integration
@pytest.mark.slow
class TestAgentWorkflow(AsyncTestCase):
    """Test complete agent workflow integration."""
    
    def setup_mocks(self):
        """Setup mocks for agent workflow tests."""
        self.mock_azure_client = AsyncMock()
        self.mock_calendar_client = AsyncMock()
        self.mock_docs_client = AsyncMock()
        self.mock_permissions = MagicMock()
        self.mock_evaluator = AsyncMock()
        
        # Setup mock responses
        self.setup_mock_responses()
    
    def setup_mock_responses(self):
        """Setup mock responses for various services."""
        # Calendar service responses
        self.mock_calendar_client.get_events.return_value = '[]'
        self.mock_calendar_client.get_rooms.return_value = '[{"id": "room1", "name": "Conference Room A"}]'
        self.mock_calendar_client.check_room_availability.return_value = '{"available": true}'
        
        # Permissions responses
        self.mock_permissions.check_permission.return_value = True
        
        # Evaluation responses
        self.mock_evaluator.evaluate_response.return_value = {
            "relevance": 0.85,
            "helpfulness": 0.90,
            "accuracy": 0.88,
            "overall_score": 0.88
        }
    
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    @pytest.mark.asyncio
    async def test_complete_scheduling_workflow(self):
        """Test complete meeting scheduling workflow."""
        # Mock agent core
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Mock agent methods
            mock_agent.initialize.return_value = True
            mock_agent.process_request.return_value = "Meeting scheduled successfully"
            mock_agent.get_available_rooms.return_value = ["Conference Room A", "Conference Room B"]
            mock_agent.schedule_meeting.return_value = "Meeting scheduled for 2024-01-15 at 10:00 AM"
            
            # Test workflow
            agent = mock_agent_class()
            
            # Step 1: Initialize agent
            init_result = await agent.initialize()
            assert init_result is True
            
            # Step 2: Get available rooms
            rooms = await agent.get_available_rooms()
            assert len(rooms) >= 2
            assert "Conference Room A" in rooms
            
            # Step 3: Schedule meeting
            meeting_result = await agent.schedule_meeting(
                title="Team Meeting",
                start_time="2024-01-15T10:00:00Z",
                end_time="2024-01-15T11:00:00Z",
                room="Conference Room A"
            )
            assert "Meeting scheduled" in meeting_result
            
            # Step 4: Process user request
            user_request = "Schedule a meeting for tomorrow at 2 PM"
            response = await agent.process_request(user_request)
            assert response == "Meeting scheduled successfully"
    
    @pytest.mark.asyncio
    async def test_room_availability_workflow(self):
        """Test room availability checking workflow."""
        with patch('services.calendar_service.SyntheticCalendarService') as mock_service:
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
                user_id=TEST_USER_ID,
                calendar_id=TEST_CALENDAR_ID,
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
        with patch('services.simple_permissions.SimplePermissions') as mock_perms_class:
            mock_perms = MagicMock()
            mock_perms_class.return_value = mock_perms
            
            # Setup mock responses
            mock_perms.check_permission.return_value = True
            mock_perms.grant_permission.return_value = True
            
            permissions = mock_perms_class()
            
            # Test permission checks
            can_read = permissions.check_permission(TEST_USER_ID, "read", "calendar")
            assert can_read is True
            
            can_write = permissions.check_permission(TEST_USER_ID, "write", "calendar")
            assert can_write is True
            
            can_book = permissions.check_permission(TEST_USER_ID, "book", "room")
            assert can_book is True
    
    @pytest.mark.asyncio
    async def test_evaluation_workflow(self):
        """Test evaluation workflow."""
        with patch('evaluation.real_time_evaluator.RealTimeEvaluator') as mock_eval_class:
            mock_evaluator = AsyncMock()
            mock_eval_class.return_value = mock_evaluator
            
            # Setup mock responses
            mock_evaluator.evaluate_response.return_value = {
                "relevance": 0.85,
                "helpfulness": 0.90,
                "accuracy": 0.88,
                "overall_score": 0.88
            }
            
            evaluator = mock_eval_class()
            
            # Test evaluation
            response = "Meeting scheduled for tomorrow at 2 PM in Conference Room A"
            context = "User requested to schedule a meeting"
            
            evaluation_result = await evaluator.evaluate_response(response, context)
            
            assert evaluation_result["relevance"] == 0.85
            assert evaluation_result["helpfulness"] == 0.90
            assert evaluation_result["accuracy"] == 0.88
            assert evaluation_result["overall_score"] == 0.88
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling throughout the workflow."""
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            # Simulate various errors
            mock_agent.initialize.side_effect = Exception("Initialization failed")
            
            agent = mock_agent_class()
            
            # Test error handling
            with pytest.raises(Exception) as exc_info:
                await agent.initialize()
            
            assert "Initialization failed" in str(exc_info.value)
            
            # Test recovery
            mock_agent.initialize.side_effect = None
            mock_agent.initialize.return_value = True
            
            init_result = await agent.initialize()
            assert init_result is True
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_workflow(self):
        """Test handling of concurrent requests."""
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class:
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
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class, \
             patch('services.mcp_client.CalendarMCPClient') as mock_mcp_class, \
             patch('services.simple_permissions.SimplePermissions') as mock_perms_class, \
             patch('evaluation.real_time_evaluator.RealTimeEvaluator') as mock_eval_class:
            
            # Setup mocks
            mock_agent = AsyncMock()
            mock_mcp = AsyncMock()
            mock_perms = MagicMock()
            mock_eval = AsyncMock()
            
            mock_agent_class.return_value = mock_agent
            mock_mcp_class.return_value = mock_mcp
            mock_perms_class.return_value = mock_perms
            mock_eval_class.return_value = mock_eval
            
            # Setup responses
            mock_agent.initialize.return_value = True
            mock_agent.process_request.return_value = "Meeting scheduled successfully"
            mock_mcp.create_event_via_mcp.return_value = {"id": "event123", "status": "created"}
            mock_perms.check_permission.return_value = True
            mock_eval.evaluate_response.return_value = {"overall_score": 0.88}
            
            # Create instances
            agent = mock_agent_class()
            mcp_client = mock_mcp_class()
            permissions = mock_perms_class()
            evaluator = mock_eval_class()
            
            # Test complete workflow
            # Step 1: Initialize
            await agent.initialize()
            
            # Step 2: Check permissions
            can_schedule = permissions.check_permission(TEST_USER_ID, "create", "event")
            assert can_schedule is True
            
            # Step 3: Process request
            response = await agent.process_request("Schedule a meeting for tomorrow")
            assert response == "Meeting scheduled successfully"
            
            # Step 4: Create event via MCP
            event_result = await mcp_client.create_event_via_mcp(
                user_id=TEST_USER_ID,
                calendar_id=TEST_CALENDAR_ID,
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
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class:
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
        
        with patch('agent_core.CalendarSchedulerAgent') as mock_agent_class:
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
        with patch('services.calendar_service.SyntheticCalendarService') as mock_service:
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
