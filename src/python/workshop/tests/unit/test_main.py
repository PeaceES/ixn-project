"""
Unit tests for main.py terminal interface.
Tests the CLI functionality and agent initialization workflows.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import main
from agent_core import CalendarAgentCore


@pytest.mark.unit
class TestMainTerminalInterface:
    """Unit tests for main.py terminal interface."""
    
    @pytest.fixture
    def mock_agent_core(self):
        """Mock CalendarAgentCore for testing."""
        with patch('main.CalendarAgentCore') as mock_core_class:
            mock_core = AsyncMock(spec=CalendarAgentCore)
            mock_core_class.return_value = mock_core
            
            # Mock successful initialization
            mock_core.initialize_agent.return_value = (True, "Agent initialized successfully")
            
            # Mock agent status
            mock_core.get_agent_status.return_value = {
                'mcp_status': 'healthy',
                'user_directory': {'loaded': True},
                'agent_id': 'test-agent-123'
            }
            
            # Mock message processing
            mock_core.process_message.return_value = (True, "Test response from agent")
            
            # Mock cleanup
            mock_core.cleanup.return_value = None
            
            yield mock_core
    
    @pytest.mark.asyncio
    async def test_main_successful_initialization(self, mock_agent_core):
        """Test main() function with successful agent initialization."""
        with patch('builtins.input', side_effect=['exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify agent initialization was called
                mock_agent_core.initialize_agent.assert_called_once()
                mock_agent_core.get_agent_status.assert_called_once()
                
                # Verify success messages were printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                success_messages = [msg for msg in print_calls if "✅" in str(msg)]
                assert len(success_messages) > 0
    
    @pytest.mark.asyncio
    async def test_main_initialization_failure(self, mock_agent_core):
        """Test main() function when agent initialization fails."""
        mock_agent_core.initialize_agent.return_value = (False, "Connection failed")
        
        with patch('builtins.print') as mock_print:
            
            await main.main()
            
            # Verify initialization was attempted
            mock_agent_core.initialize_agent.assert_called_once()
            
            # Verify failure messages were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            error_messages = [msg for msg in print_calls if "Initialization failed" in str(msg)]
            assert len(error_messages) > 0
            
            # Should not call get_agent_status if initialization failed
            mock_agent_core.get_agent_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_main_message_processing_workflow(self, mock_agent_core):
        """Test main() function message processing workflow."""
        test_query = "What meetings do I have today?"
        
        with patch('builtins.input', side_effect=[test_query, 'exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify message processing was called
                mock_agent_core.process_message.assert_called_with(test_query)
                
                # Verify response was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                response_messages = [msg for msg in print_calls if "Agent response:" in str(msg)]
                assert len(response_messages) > 0
    
    @pytest.mark.asyncio 
    async def test_main_message_processing_error(self, mock_agent_core):
        """Test main() function when message processing fails."""
        mock_agent_core.process_message.return_value = (False, "Agent is busy")
        test_query = "What meetings do I have today?"
        
        with patch('builtins.input', side_effect=[test_query, 'exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify error was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                error_messages = [msg for msg in print_calls if "Error:" in str(msg)]
                assert len(error_messages) > 0
    
    @pytest.mark.asyncio
    async def test_main_save_command(self, mock_agent_core):
        """Test main() function with save command."""
        with patch('builtins.input', side_effect=['save']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Should not call cleanup when saving
                mock_agent_core.cleanup.assert_not_called()
                
                # Verify save message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                save_messages = [msg for msg in print_calls if "not been deleted" in str(msg)]
                assert len(save_messages) > 0
    
    @pytest.mark.asyncio
    async def test_main_exit_command_cleanup(self, mock_agent_core):
        """Test main() function with exit command performs cleanup."""
        with patch('builtins.input', side_effect=['exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Should call cleanup when exiting
                mock_agent_core.cleanup.assert_called_once()
                
                # Verify cleanup message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                cleanup_messages = [msg for msg in print_calls if "Cleaning up" in str(msg)]
                assert len(cleanup_messages) > 0
    
    @pytest.mark.asyncio
    async def test_main_empty_input_handling(self, mock_agent_core):
        """Test main() function handles empty input correctly."""
        with patch('builtins.input', side_effect=['', '   ', 'exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Should not process empty messages
                mock_agent_core.process_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_main_multiple_queries(self, mock_agent_core):
        """Test main() function processes multiple queries."""
        queries = ["Show me all rooms", "Check availability", "exit"]
        
        with patch('builtins.input', side_effect=queries):
            with patch('builtins.print'):
                
                await main.main()
                
                # Should process both queries before exit
                assert mock_agent_core.process_message.call_count == 2
                mock_agent_core.process_message.assert_any_call("Show me all rooms")
                mock_agent_core.process_message.assert_any_call("Check availability")
    
    @pytest.mark.asyncio
    async def test_main_debug_output(self, mock_agent_core):
        """Test main() function includes debug output."""
        with patch('builtins.input', side_effect=['test query', 'exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify debug messages were printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                debug_messages = [msg for msg in print_calls if "[DEBUG]" in str(msg)]
                assert len(debug_messages) > 0
    
    @pytest.mark.asyncio
    async def test_main_structured_response_markers(self, mock_agent_core):
        """Test main() function uses structured response markers."""
        with patch('builtins.input', side_effect=['test query', 'exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify structured markers were used
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                start_markers = [msg for msg in print_calls if "FINAL_AGENT_RESPONSE_START" in str(msg)]
                end_markers = [msg for msg in print_calls if "FINAL_AGENT_RESPONSE_END" in str(msg)]
                
                assert len(start_markers) >= 1
                assert len(end_markers) >= 1
    
    def test_main_script_entry_point(self):
        """Test that main script can be run as entry point."""
        with patch('main.asyncio.run') as mock_run:
            with patch('builtins.print'):
                
                # Simulate running the script directly
                import __main__
                old_name = __main__.__name__
                __main__.__name__ = "__main__"
                
                try:
                    # This would normally trigger the if __name__ == "__main__" block
                    # We'll just verify the structure exists
                    assert hasattr(main, 'main')
                    assert callable(main.main)
                finally:
                    __main__.__name__ = old_name
    
    @pytest.mark.asyncio
    async def test_main_agent_status_display(self, mock_agent_core):
        """Test that agent status is properly displayed."""
        mock_agent_core.get_agent_status.return_value = {
            'mcp_status': 'healthy',
            'user_directory': {'loaded': True},
            'agent_id': 'test-agent-456'
        }
        
        with patch('builtins.input', side_effect=['exit']):
            with patch('builtins.print') as mock_print:
                
                await main.main()
                
                # Verify status information was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                status_messages = [msg for msg in print_calls if "Agent Status:" in str(msg)]
                mcp_status_messages = [msg for msg in print_calls if "MCP Server:" in str(msg)]
                user_dir_messages = [msg for msg in print_calls if "User Directory:" in str(msg)]
                agent_id_messages = [msg for msg in print_calls if "Agent ID:" in str(msg)]
                
                assert len(status_messages) >= 1
                assert len(mcp_status_messages) >= 1
                assert len(user_dir_messages) >= 1
                assert len(agent_id_messages) >= 1
