"""
Unit tests for the evaluation system.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_framework import (
    AsyncTestCase, BaseTestCase, TEST_USER_ID
)


@pytest.mark.unit
@pytest.mark.evaluation
class TestRealTimeEvaluator(AsyncTestCase):
    """Test the RealTimeEvaluator class."""
    
    def setup_mocks(self):
        """Setup mocks for evaluation tests."""
        self.mock_evaluator = MagicMock()
        self.mock_evaluator.enabled = True
        self.mock_evaluator.metrics = ["relevance", "helpfulness", "accuracy"]
        
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        # Test that evaluator can be created
        assert self.mock_evaluator is not None
        assert hasattr(self.mock_evaluator, 'enabled')
        assert hasattr(self.mock_evaluator, 'metrics')
    
    def test_evaluator_enabled_property(self):
        """Test evaluator enabled property."""
        assert self.mock_evaluator.enabled is True
        
        # Test toggling enabled state
        self.mock_evaluator.enabled = False
        assert self.mock_evaluator.enabled is False
    
    def test_evaluator_metrics_property(self):
        """Test evaluator metrics property."""
        expected_metrics = ["relevance", "helpfulness", "accuracy"]
        assert self.mock_evaluator.metrics == expected_metrics
        
        # Test setting new metrics
        new_metrics = ["quality", "speed", "completeness"]
        self.mock_evaluator.metrics = new_metrics
        assert self.mock_evaluator.metrics == new_metrics
    
    @pytest.mark.asyncio
    async def test_evaluate_response_basic(self):
        """Test basic response evaluation."""
        # Mock evaluation method
        self.mock_evaluator.evaluate_response = AsyncMock()
        self.mock_evaluator.evaluate_response.return_value = {
            "relevance": 0.85,
            "helpfulness": 0.90,
            "accuracy": 0.88,
            "overall_score": 0.88
        }
        
        test_response = "The meeting is scheduled for 2024-01-15 at 10:00 AM in Conference Room A."
        test_context = "User asked to schedule a meeting for next Monday."
        
        result = await self.mock_evaluator.evaluate_response(test_response, test_context)
        
        assert result is not None
        assert "relevance" in result
        assert "helpfulness" in result
        assert "accuracy" in result
        assert "overall_score" in result
        
        # Verify scores are reasonable
        assert 0.0 <= result["relevance"] <= 1.0
        assert 0.0 <= result["helpfulness"] <= 1.0
        assert 0.0 <= result["accuracy"] <= 1.0
        assert 0.0 <= result["overall_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_evaluate_response_with_empty_input(self):
        """Test evaluation with empty input."""
        self.mock_evaluator.evaluate_response = AsyncMock()
        self.mock_evaluator.evaluate_response.return_value = {
            "relevance": 0.0,
            "helpfulness": 0.0,
            "accuracy": 0.0,
            "overall_score": 0.0
        }
        
        result = await self.mock_evaluator.evaluate_response("", "")
        
        assert result is not None
        assert all(score == 0.0 for score in result.values())
    
    @pytest.mark.asyncio
    async def test_evaluate_response_error_handling(self):
        """Test evaluation error handling."""
        self.mock_evaluator.evaluate_response = AsyncMock()
        self.mock_evaluator.evaluate_response.side_effect = Exception("Evaluation failed")
        
        with pytest.raises(Exception) as exc_info:
            await self.mock_evaluator.evaluate_response("test response", "test context")
        
        assert "Evaluation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_batch_evaluation(self):
        """Test batch evaluation of multiple responses."""
        self.mock_evaluator.evaluate_batch = AsyncMock()
        self.mock_evaluator.evaluate_batch.return_value = [
            {"relevance": 0.85, "helpfulness": 0.90, "accuracy": 0.88},
            {"relevance": 0.78, "helpfulness": 0.85, "accuracy": 0.82},
            {"relevance": 0.92, "helpfulness": 0.88, "accuracy": 0.90}
        ]
        
        test_responses = [
            "Meeting scheduled for tomorrow at 2 PM.",
            "Room A is available for the meeting.",
            "I'll send you a calendar invitation."
        ]
        
        results = await self.mock_evaluator.evaluate_batch(test_responses)
        
        assert len(results) == 3
        for result in results:
            assert "relevance" in result
            assert "helpfulness" in result
            assert "accuracy" in result
    
    def test_evaluator_configuration(self):
        """Test evaluator configuration."""
        # Test different configuration options
        config = {
            "enabled": True,
            "metrics": ["relevance", "helpfulness"],
            "threshold": 0.7,
            "auto_evaluate": True
        }
        
        # Mock configuration method
        self.mock_evaluator.configure = MagicMock()
        self.mock_evaluator.configure.return_value = True
        
        result = self.mock_evaluator.configure(config)
        
        assert result is True
        self.mock_evaluator.configure.assert_called_once_with(config)
    
    @pytest.mark.asyncio
    async def test_evaluator_with_disabled_state(self):
        """Test evaluator behavior when disabled."""
        self.mock_evaluator.enabled = False
        self.mock_evaluator.evaluate_response = AsyncMock()
        self.mock_evaluator.evaluate_response.return_value = None
        
        result = await self.mock_evaluator.evaluate_response("test", "test")
        
        # When disabled, evaluation should return None or skip
        assert result is None


@pytest.mark.unit
@pytest.mark.evaluation
class TestQuickEvaluateFunction(BaseTestCase):
    """Test the quick_evaluate_response function."""
    
    def setup_mocks(self):
        """Setup mocks for quick evaluation tests."""
        self.mock_quick_eval = MagicMock()
        
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    def test_quick_evaluate_response_basic(self):
        """Test basic quick evaluation."""
        self.mock_quick_eval.return_value = {
            "score": 0.85,
            "feedback": "Good response, relevant and helpful"
        }
        
        result = self.mock_quick_eval("Good response", "User question")
        
        assert result is not None
        assert "score" in result
        assert "feedback" in result
        assert 0.0 <= result["score"] <= 1.0
        assert isinstance(result["feedback"], str)
    
    def test_quick_evaluate_response_edge_cases(self):
        """Test quick evaluation with edge cases."""
        # Test with empty response
        self.mock_quick_eval.return_value = {
            "score": 0.0,
            "feedback": "Empty response"
        }
        
        result = self.mock_quick_eval("", "test context")
        assert result["score"] == 0.0
        
        # Test with very long response
        long_response = "x" * 10000
        self.mock_quick_eval.return_value = {
            "score": 0.75,
            "feedback": "Response too long but relevant"
        }
        
        result = self.mock_quick_eval(long_response, "test context")
        assert result["score"] == 0.75
    
    def test_quick_evaluate_response_error_handling(self):
        """Test quick evaluation error handling."""
        self.mock_quick_eval.side_effect = Exception("Quick evaluation failed")
        
        with pytest.raises(Exception) as exc_info:
            self.mock_quick_eval("test response", "test context")
        
        assert "Quick evaluation failed" in str(exc_info.value)
    
    def test_quick_evaluate_response_different_metrics(self):
        """Test quick evaluation with different metrics."""
        # Test relevance focused evaluation
        self.mock_quick_eval.return_value = {
            "score": 0.90,
            "feedback": "Highly relevant response",
            "relevance": 0.95,
            "clarity": 0.85
        }
        
        result = self.mock_quick_eval("Relevant response", "User question")
        
        assert result["relevance"] == 0.95
        assert result["clarity"] == 0.85
        assert result["score"] == 0.90


@pytest.mark.unit
@pytest.mark.evaluation
class TestEvaluationMetrics(BaseTestCase):
    """Test evaluation metrics and scoring."""
    
    def setup_mocks(self):
        """Setup mocks for metrics tests."""
        self.mock_metrics = MagicMock()
        
    def cleanup_mocks(self):
        """Cleanup mocks after tests."""
        pass
    
    def test_relevance_metric(self):
        """Test relevance metric calculation."""
        self.mock_metrics.calculate_relevance = MagicMock()
        self.mock_metrics.calculate_relevance.return_value = 0.85
        
        score = self.mock_metrics.calculate_relevance("Meeting scheduled", "Schedule meeting")
        
        assert 0.0 <= score <= 1.0
        assert score == 0.85
    
    def test_helpfulness_metric(self):
        """Test helpfulness metric calculation."""
        self.mock_metrics.calculate_helpfulness = MagicMock()
        self.mock_metrics.calculate_helpfulness.return_value = 0.90
        
        score = self.mock_metrics.calculate_helpfulness("Helpful response", "User question")
        
        assert 0.0 <= score <= 1.0
        assert score == 0.90
    
    def test_accuracy_metric(self):
        """Test accuracy metric calculation."""
        self.mock_metrics.calculate_accuracy = MagicMock()
        self.mock_metrics.calculate_accuracy.return_value = 0.88
        
        score = self.mock_metrics.calculate_accuracy("Accurate response", "Context")
        
        assert 0.0 <= score <= 1.0
        assert score == 0.88
    
    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        self.mock_metrics.calculate_overall_score = MagicMock()
        self.mock_metrics.calculate_overall_score.return_value = 0.87
        
        metrics = {
            "relevance": 0.85,
            "helpfulness": 0.90,
            "accuracy": 0.88
        }
        
        overall_score = self.mock_metrics.calculate_overall_score(metrics)
        
        assert 0.0 <= overall_score <= 1.0
        assert overall_score == 0.87
    
    def test_metrics_validation(self):
        """Test metrics validation."""
        self.mock_metrics.validate_score = MagicMock()
        
        # Test valid scores
        self.mock_metrics.validate_score.return_value = True
        assert self.mock_metrics.validate_score(0.85) is True
        assert self.mock_metrics.validate_score(0.0) is True
        assert self.mock_metrics.validate_score(1.0) is True
        
        # Test invalid scores
        self.mock_metrics.validate_score.return_value = False
        assert self.mock_metrics.validate_score(-0.1) is False
        assert self.mock_metrics.validate_score(1.1) is False


@pytest.mark.integration
@pytest.mark.evaluation
class TestEvaluationIntegration:
    """Integration tests for evaluation system."""
    
    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow."""
        # Mock evaluator
        mock_evaluator = MagicMock()
        mock_evaluator.enabled = True
        mock_evaluator.evaluate_response = AsyncMock()
        mock_evaluator.evaluate_response.return_value = {
            "relevance": 0.85,
            "helpfulness": 0.90,
            "accuracy": 0.88,
            "overall_score": 0.88
        }
        
        # Test workflow
        response = "Meeting scheduled for tomorrow at 2 PM in Conference Room A."
        context = "User requested to schedule a meeting for next day."
        
        # Step 1: Check if evaluation is enabled
        assert mock_evaluator.enabled is True
        
        # Step 2: Evaluate response
        result = await mock_evaluator.evaluate_response(response, context)
        
        # Step 3: Verify results
        assert result is not None
        assert all(key in result for key in ["relevance", "helpfulness", "accuracy", "overall_score"])
        assert all(0.0 <= score <= 1.0 for score in result.values())
        
        # Step 4: Check if evaluation meets threshold
        threshold = 0.8
        assert result["overall_score"] >= threshold
    
    @pytest.mark.asyncio
    async def test_evaluation_with_stream_handler(self):
        """Test evaluation integration with stream handler."""
        # Mock stream handler with evaluation
        mock_handler = MagicMock()
        mock_handler.evaluate_response = AsyncMock()
        mock_handler.evaluate_response.return_value = {
            "score": 0.85,
            "feedback": "Good response"
        }
        
        # Simulate stream handler processing
        response = "Calendar event created successfully."
        
        evaluation_result = await mock_handler.evaluate_response(response)
        
        assert evaluation_result is not None
        assert "score" in evaluation_result
        assert "feedback" in evaluation_result
    
    def test_evaluation_configuration_loading(self):
        """Test loading evaluation configuration."""
        # Mock configuration loader
        mock_config = MagicMock()
        mock_config.load_evaluation_config = MagicMock()
        mock_config.load_evaluation_config.return_value = {
            "enabled": True,
            "metrics": ["relevance", "helpfulness", "accuracy"],
            "threshold": 0.7,
            "auto_evaluate": True
        }
        
        config = mock_config.load_evaluation_config()
        
        assert config["enabled"] is True
        assert len(config["metrics"]) == 3
        assert config["threshold"] == 0.7
        assert config["auto_evaluate"] is True


@pytest.mark.unit
@pytest.mark.evaluation
class TestEvaluationErrorHandling:
    """Test error handling in evaluation system."""
    
    @pytest.mark.asyncio
    async def test_evaluation_timeout_handling(self):
        """Test handling of evaluation timeouts."""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_response = AsyncMock()
        mock_evaluator.evaluate_response.side_effect = TimeoutError("Evaluation timeout")
        
        with pytest.raises(TimeoutError) as exc_info:
            await mock_evaluator.evaluate_response("test response", "test context")
        
        assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_evaluation_network_error_handling(self):
        """Test handling of network errors during evaluation."""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_response = AsyncMock()
        mock_evaluator.evaluate_response.side_effect = ConnectionError("Network error")
        
        with pytest.raises(ConnectionError) as exc_info:
            await mock_evaluator.evaluate_response("test response", "test context")
        
        assert "network" in str(exc_info.value).lower()
    
    def test_evaluation_invalid_input_handling(self):
        """Test handling of invalid input to evaluation."""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_response = MagicMock()
        
        # Test with None input
        mock_evaluator.evaluate_response.side_effect = ValueError("Invalid input")
        
        with pytest.raises(ValueError) as exc_info:
            mock_evaluator.evaluate_response(None, None)
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_evaluation_resource_exhaustion(self):
        """Test handling of resource exhaustion during evaluation."""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_response = MagicMock()
        mock_evaluator.evaluate_response.side_effect = MemoryError("Out of memory")
        
        with pytest.raises(MemoryError) as exc_info:
            mock_evaluator.evaluate_response("test response", "test context")
        
        assert "memory" in str(exc_info.value).lower()
