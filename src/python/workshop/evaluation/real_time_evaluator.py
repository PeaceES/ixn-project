"""
Lightweight evaluation module for real-time agent assessment.

This module provides simplified evaluation that can be run quickly
after each agent response to provide immediate feedback.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import evaluation components
from azure.ai.evaluation import (
    AIAgentConverter,
    IntentResolutionEvaluator,
    ToolCallAccuracyEvaluator,
    CoherenceEvaluator
)
from azure.ai.projects.models import ConnectionType

load_dotenv()

# Configuration
ENABLE_AUTO_EVALUATION = os.getenv("ENABLE_AUTO_EVALUATION", "false").lower() == "true"
AUTO_EVAL_METRICS = os.getenv("AUTO_EVAL_METRICS", "intent,coherence,tools").split(",")

logger = logging.getLogger(__name__)

class RealTimeEvaluator:
    """Lightweight evaluator for real-time assessment of agent responses."""
    
    def __init__(self, project_client=None):
        """Initialize the real-time evaluator."""
        self.project_client = project_client
        self.converter = None
        self.evaluators = {}
        self.initialized = False
        self.enabled = ENABLE_AUTO_EVALUATION
        self.metrics = [metric.strip() for metric in AUTO_EVAL_METRICS]
        
    async def _initialize_evaluators(self):
        """Initialize evaluators lazily when first needed."""
        if self.initialized:
            return
            
        if not self.project_client:
            logger.error("Project client is required for initialization")
            return
            
        try:
            # Initialize converter
            self.converter = AIAgentConverter(self.project_client)
            logger.info("AIAgentConverter initialized")
            
            # Get model configuration
            model_config = await self.project_client.connections.get_default(
                connection_type=ConnectionType.AZURE_OPEN_AI,
                include_credentials=True
            )
            logger.info("Retrieved model configuration")
            
            model_config = model_config.to_evaluator_model_config(
                deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4"),
                api_version="2023-05-15",
                include_credentials=True
            )
            logger.info("Model configuration prepared for evaluators")
            
            # Initialize only one evaluator at a time to avoid timeout
            # Start with the most important one
            if "coherence" in AUTO_EVAL_METRICS:
                try:
                    self.evaluators["coherence"] = CoherenceEvaluator(model_config=model_config)
                    logger.info("Coherence evaluator initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize coherence evaluator: {e}")
            
            # Mark as initialized even if only one evaluator works
            self.initialized = True
            logger.info(f"Real-time evaluators initialized successfully ({len(self.evaluators)} evaluators)")
            
        except Exception as e:
            logger.error(f"Failed to initialize evaluators: {e}")
            logger.error(f"Error type: {type(e)}")
            self.initialized = False
    
    async def evaluate_response(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Quickly evaluate a single agent response.
        
        Args:
            thread_id: The thread ID of the conversation
            run_id: The run ID of the agent response
            
        Returns:
            Dictionary with evaluation scores and summary
        """
        if not ENABLE_AUTO_EVALUATION:
            return {"enabled": False}
            
        try:
            # Initialize evaluators if needed
            await self._initialize_evaluators()
            
            if not self.initialized:
                logger.warning("Evaluators not initialized, skipping evaluation")
                return {"error": "Evaluators not initialized"}
            
            logger.info(f"Starting evaluation for thread {thread_id}, run {run_id}")
            
            # Convert agent data with proper error handling
            try:
                logger.info("Converting agent data...")
                converted_data = await self.converter.convert(thread_id, run_id)
                logger.info(f"Conversion completed, data type: {type(converted_data)}")
                
                # Handle the converted data properly - it might be a list or dict
                if hasattr(converted_data, '__iter__') and not isinstance(converted_data, (str, dict)):
                    # If it's iterable (like a list), take the first item
                    converted_data_list = list(converted_data)
                    logger.info(f"Converted data is iterable with {len(converted_data_list)} items")
                    converted_data = converted_data_list[0] if converted_data_list else {}
                    
            except Exception as e:
                logger.error(f"Data conversion failed: {e}")
                return {"error": f"Data conversion failed: {e}"}
            
            # Ensure converted_data is a dictionary
            if not isinstance(converted_data, dict):
                logger.error(f"Expected dict, got {type(converted_data)}")
                return {"error": "Invalid data format from converter"}
            
            logger.info(f"Converted data keys: {list(converted_data.keys())}")
            
            # Run evaluations
            results = {}
            scores = []
            
            for name, evaluator in self.evaluators.items():
                try:
                    logger.info(f"Running {name} evaluator...")
                    
                    # Skip tool evaluator if no tool calls
                    if name == "tools" and not self._has_tool_calls(converted_data):
                        logger.info(f"Skipping {name} evaluator - no tool calls detected")
                        continue
                    
                    # Call evaluator with proper arguments
                    if hasattr(evaluator, '__call__'):
                        # For newer SDK versions, evaluators might be callable
                        result = evaluator(**converted_data)
                    else:
                        # For older versions, they might have an evaluate method
                        result = evaluator.evaluate(**converted_data)
                    
                    # Handle async results
                    if hasattr(result, '__await__'):
                        result = await result
                    
                    logger.info(f"{name} evaluator completed with result type: {type(result)}")
                    results[name] = result
                    
                    # Extract score for summary
                    score = self._extract_score(result, name)
                    if score is not None:
                        scores.append(score)
                        logger.info(f"{name} evaluator score: {score}")
                    else:
                        logger.warning(f"Could not extract score from {name} evaluator result")
                        
                except Exception as e:
                    logger.error(f"Evaluator {name} failed: {e}")
                    results[name] = {"error": str(e)}
            
            # Calculate average score
            avg_score = sum(scores) / len(scores) if scores else 0
            
            return {
                "enabled": True,
                "average_score": avg_score,
                "total_evaluators": len(results),
                "successful_evaluators": len(scores),
                "results": results,
                "summary": self._generate_summary(results)
            }
            
        except Exception as e:
            logger.error(f"Real-time evaluation failed: {e}")
            return {"error": str(e), "enabled": False}
    
    def _has_tool_calls(self, converted_data: Dict[str, Any]) -> bool:
        """Check if the response contains tool calls."""
        try:
            # Check different possible structures for tool calls
            # Method 1: Check in response field
            response = converted_data.get("response", "")
            if isinstance(response, list):
                for message in response:
                    if isinstance(message, dict) and message.get("role") == "assistant":
                        content = message.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "tool_call":
                                    return True
            
            # Method 2: Check in messages field
            messages = converted_data.get("messages", [])
            if isinstance(messages, list):
                for message in messages:
                    if isinstance(message, dict):
                        # Check for tool_calls field
                        if message.get("tool_calls"):
                            return True
                        # Check for function_call field
                        if message.get("function_call"):
                            return True
            
            # Method 3: Check for any field containing "tool" or "function"
            for key, value in converted_data.items():
                if "tool" in key.lower() or "function" in key.lower():
                    if value:  # Non-empty value
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking tool calls: {e}")
            return False  # Default to False on error
    
    def _extract_score(self, result: Dict[str, Any], evaluator_name: str) -> Optional[float]:
        """Extract numerical score from evaluator result."""
        if not isinstance(result, dict) or result.get("error"):
            return None
            
        try:
            # Try multiple possible score field names for each evaluator
            score_fields_map = {
                "intent": ["intent_resolution", "intent_score", "intent", "score"],
                "coherence": ["coherence", "coherence_score", "score"],
                "tools": ["tool_call_accuracy", "tool_accuracy", "accuracy", "score"]
            }
            
            possible_fields = score_fields_map.get(evaluator_name, ["score"])
            
            for field in possible_fields:
                if field in result:
                    score = result[field]
                    if isinstance(score, (int, float)):
                        return float(score)
                    elif isinstance(score, str):
                        try:
                            return float(score)
                        except ValueError:
                            continue
            
            # If no specific field found, try to find any numeric field
            for key, value in result.items():
                if isinstance(value, (int, float)) and key.lower() not in ["error", "timestamp"]:
                    return float(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting score for {evaluator_name}: {e}")
            return None
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of evaluation results."""
        if not results:
            return "No evaluation results"
        
        summary_parts = []
        
        for name, result in results.items():
            if isinstance(result, dict) and not result.get("error"):
                score = self._extract_score(result, name)
                if score is not None:
                    if name == "intent":
                        summary_parts.append(f"Intent: {score:.1f}/5")
                    elif name == "coherence":
                        summary_parts.append(f"Coherence: {score:.1f}/5")
                    elif name == "tools":
                        summary_parts.append(f"Tools: {score:.1%}")
        
        return " | ".join(summary_parts) if summary_parts else "No scores available"

# Global instance (will be initialized when needed)
_real_time_evaluator = None

async def get_real_time_evaluator(project_client):
    """Get or create the global real-time evaluator instance."""
    global _real_time_evaluator
    if _real_time_evaluator is None:
        _real_time_evaluator = RealTimeEvaluator(project_client)
    return _real_time_evaluator

async def quick_evaluate_response(project_client, thread_id: str, run_id: str) -> Dict[str, Any]:
    """
    Convenience function to quickly evaluate a response.
    
    Args:
        project_client: Azure AI project client
        thread_id: Thread ID of the conversation
        run_id: Run ID of the agent response
        
    Returns:
        Evaluation results dictionary
    """
    evaluator = await get_real_time_evaluator(project_client)
    return await evaluator.evaluate_response(thread_id, run_id)
