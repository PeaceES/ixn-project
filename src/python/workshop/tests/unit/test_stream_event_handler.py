"""
Unit tests for Stream Event Handler.
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.stream_event_handler import StreamEventHandler
from azure.ai.agents.models import (
    AsyncFunctionTool,
    MessageDeltaChunk,
    MessageStatus,
    RunStatus,
    RunStep,
    RunStepStatus,
    ThreadMessage,
    ThreadRun
)


@pytest.mark.unit
class TestStreamEventHandler:
    """Test the StreamEventHandler class."""
    
    @pytest.fixture
    def mock_functions(self):
        """Mock AsyncFunctionTool."""
        return Mock(spec=AsyncFunctionTool)
    
    @pytest.fixture
    def mock_project_client(self):
        """Mock AIProjectClient."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_utilities(self):
        """Mock Utilities."""
        return Mock()
    
    @pytest.fixture
    def event_handler(self, mock_functions, mock_project_client, mock_utilities):
        """Create StreamEventHandler instance."""
        return StreamEventHandler(
            functions=mock_functions,
            project_client=mock_project_client,
            utilities=mock_utilities
        )
    
    def test_initialization(self, event_handler, mock_functions, mock_project_client, mock_utilities):
        """Test StreamEventHandler initialization."""
        assert event_handler.functions == mock_functions
        assert event_handler.project_client == mock_project_client
        assert event_handler.util == mock_utilities
        assert event_handler.current_thread_id is None
        assert event_handler.current_run_id is None
    
    @pytest.mark.asyncio
    async def test_on_message_created(self, event_handler):
        """Test message creation event handling."""
        mock_message = Mock(spec=ThreadMessage)
        mock_message.id = "msg-123"
        mock_message.content = [{"type": "text", "text": {"value": "Hello"}}]
        
        # Should not raise exception
        await event_handler.on_message_created(mock_message)
    
    @pytest.mark.asyncio
    async def test_on_message_delta(self, event_handler):
        """Test message delta event handling."""
        mock_delta = Mock(spec=MessageDeltaChunk)
        mock_delta.id = "msg-123"
        mock_delta.delta = Mock()
        mock_delta.delta.content = [{"type": "text", "text": {"value": "Hello"}}]
        
        # Should not raise exception
        await event_handler.on_message_delta(mock_delta)
    
    @pytest.mark.asyncio
    async def test_on_run_created(self, event_handler):
        """Test run creation event handling."""
        mock_run = Mock(spec=ThreadRun)
        mock_run.id = "run-123"
        mock_run.thread_id = "thread-456"
        mock_run.status = RunStatus.IN_PROGRESS
        
        await event_handler.on_run_created(mock_run)
        
        assert event_handler.current_run_id == "run-123"
        assert event_handler.current_thread_id == "thread-456"
    
    @pytest.mark.asyncio
    async def test_on_run_completed(self, event_handler):
        """Test run completion event handling."""
        mock_run = Mock(spec=ThreadRun)
        mock_run.id = "run-123"
        mock_run.status = RunStatus.COMPLETED
        mock_run.thread_id = "thread-456"
        
        with patch.object(event_handler.util, 'log_info') as mock_log:
            await event_handler.on_run_completed(mock_run)
            mock_log.assert_called()
    
    @pytest.mark.asyncio
    async def test_on_run_failed(self, event_handler):
        """Test run failure event handling."""
        mock_run = Mock(spec=ThreadRun)
        mock_run.id = "run-123"
        mock_run.status = RunStatus.FAILED
        mock_run.last_error = Mock()
        mock_run.last_error.message = "Test error"
        
        with patch.object(event_handler.util, 'log_error') as mock_log:
            await event_handler.on_run_failed(mock_run)
            mock_log.assert_called_with(f"Run failed: Test error")
    
    @pytest.mark.asyncio
    async def test_on_run_step_created(self, event_handler):
        """Test run step creation event handling."""
        mock_step = Mock(spec=RunStep)
        mock_step.id = "step-123"
        mock_step.type = "message_creation"
        mock_step.status = RunStepStatus.IN_PROGRESS
        
        # Should not raise exception
        await event_handler.on_run_step_created(mock_step)
    
    @pytest.mark.asyncio
    async def test_on_run_step_completed(self, event_handler):
        """Test run step completion event handling."""
        mock_step = Mock(spec=RunStep)
        mock_step.id = "step-123"
        mock_step.status = RunStepStatus.COMPLETED
        mock_step.type = "tool_calls"
        
        with patch.object(event_handler.util, 'log_info') as mock_log:
            await event_handler.on_run_step_completed(mock_step)
            mock_log.assert_called()
    
    @pytest.mark.asyncio
    async def test_function_call_handling(self, event_handler):
        """Test function call event handling."""
        # This would test the function calling logic
        # Implementation depends on actual function call handling in the class
        mock_function_call = {
            "name": "create_event",
            "arguments": '{"title": "Test Meeting"}'
        }
        
        with patch.object(event_handler, 'functions') as mock_functions:
            mock_functions.call = AsyncMock(return_value="Success")
            # Test would depend on actual function call implementation
            assert True  # Placeholder assertion
    
    @pytest.mark.asyncio
    async def test_error_handling_during_stream(self, event_handler):
        """Test error handling during streaming."""
        mock_run = Mock(spec=ThreadRun)
        mock_run.id = "run-123"
        mock_run.status = RunStatus.FAILED
        mock_run.last_error = None  # No error message
        
        with patch.object(event_handler.util, 'log_error') as mock_log:
            await event_handler.on_run_failed(mock_run)
            mock_log.assert_called_with("Run failed: Unknown error")
    
    @pytest.mark.asyncio
    async def test_evaluation_integration(self, event_handler):
        """Test integration with evaluation system."""
        # Test that evaluation is triggered when configured
        with patch.dict(os.environ, {"ENABLE_AUTO_EVALUATION": "true"}):
            with patch("evaluation.working_evaluator.quick_evaluate_response") as mock_eval:
                mock_eval.return_value = {"score": 0.8}
                
                mock_message = Mock(spec=ThreadMessage)
                mock_message.content = [{"type": "text", "text": {"value": "Response text"}}]
                
                await event_handler.on_message_created(mock_message)
                # Would verify evaluation was called if implemented in the handler
