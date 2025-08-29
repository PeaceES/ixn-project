"""
Hybrid evaluation module that uses Azure AI evaluators with fallback to simple evaluation.

This module provides both Azure AI evaluation and simple fallback evaluation
for immediate response assessment.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import re
import json

# Try to import Azure AI evaluation components
try:
    from azure.ai.evaluation import (
        AIAgentConverter,
        IntentResolutionEvaluator,
        ToolCallAccuracyEvaluator,
        CoherenceEvaluator
    )
    from azure.ai.projects.models import ConnectionType
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False

load_dotenv()

# Configuration
ENABLE_AUTO_EVALUATION = os.getenv("ENABLE_AUTO_EVALUATION", "false").lower() == "true"
AUTO_EVAL_METRICS = os.getenv("AUTO_EVAL_METRICS", "intent,coherence,tools").split(",")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

logger = logging.getLogger(__name__)

class HybridRealTimeEvaluator:
    """Hybrid evaluator that uses Azure AI evaluators with simple fallback."""
    
    def __init__(self, project_client=None):
        """Initialize the hybrid evaluator."""
        self.project_client = project_client
        self.converter = None
        self.azure_evaluators = {}
        self.azure_initialized = False
        self.enabled = ENABLE_AUTO_EVALUATION
        self.metrics = [metric.strip() for metric in AUTO_EVAL_METRICS]
        
    async def _initialize_azure_evaluators(self):
        """Initialize Azure AI evaluators (with timeout)."""
        if self.azure_initialized or not AZURE_AI_AVAILABLE or not self.project_client:
            return
            
        try:
            # Set a timeout for initialization
            await asyncio.wait_for(self._do_azure_initialization(), timeout=10.0)
            self.azure_initialized = True
            logger.info("Azure AI evaluators initialized successfully")
            
        except asyncio.TimeoutError:
            logger.warning("Azure AI evaluator initialization timed out, using fallback")
            self.azure_initialized = False
        except Exception as e:
            logger.error(f"Azure AI evaluator initialization failed: {e}")
            self.azure_initialized = False
    
    async def _do_azure_initialization(self):
        """Perform Azure AI evaluator initialization."""
        # Initialize converter
        self.converter = AIAgentConverter(self.project_client)
        
        # Get model configuration
        model_config = await self.project_client.connections.get_default(
            connection_type=ConnectionType.AZURE_OPEN_AI,
            include_credentials=True
        )
        model_config = model_config.to_evaluator_model_config(
            deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5-chat"),
            api_version=API_VERSION,
            include_credentials=True
        )
        
        # Initialize just one evaluator for now
        if "coherence" in AUTO_EVAL_METRICS:
            self.azure_evaluators["coherence"] = CoherenceEvaluator(model_config=model_config)
    
    async def evaluate_response(self, thread_id: str, run_id: str, response_text: str = None, user_query: str = None) -> Dict[str, Any]:
        """
        Evaluate a single agent response using Azure AI or fallback evaluation.
        
        Args:
            thread_id: The thread ID of the conversation
            run_id: The run ID of the agent response
            response_text: The agent's response text (for fallback)
            user_query: The user's query (for fallback)
            
        Returns:
            Dictionary with evaluation scores and summary
        """
        if not ENABLE_AUTO_EVALUATION:
            return {"enabled": False}
            
        # Try Azure AI evaluation first
        azure_result = await self._try_azure_evaluation(thread_id, run_id)
        if azure_result.get("success"):
            return azure_result
        
        # Fall back to simple evaluation
        logger.info("Using fallback evaluation")
        fallback_result = self._simple_evaluation(response_text, user_query)
        logger.info(f"Fallback evaluation result: {fallback_result}")
        return fallback_result
    
    async def _try_azure_evaluation(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Try Azure AI evaluation."""
        try:
            # Initialize if needed
            await self._initialize_azure_evaluators()
            
            if not self.azure_initialized:
                return {"success": False, "error": "Azure evaluators not initialized"}
            
            # Convert agent data
            converted_data = await self.converter.convert(thread_id, run_id)
            
            # Handle the converted data
            if hasattr(converted_data, '__iter__') and not isinstance(converted_data, (str, dict)):
                converted_data_list = list(converted_data)
                converted_data = converted_data_list[0] if converted_data_list else {}
            
            if not isinstance(converted_data, dict):
                return {"success": False, "error": "Invalid data format"}
            
            # Run evaluations
            results = {}
            scores = []
            
            for name, evaluator in self.azure_evaluators.items():
                try:
                    result = evaluator(**converted_data)
                    if hasattr(result, '__await__'):
                        result = await result
                    
                    results[name] = result
                    score = self._extract_score(result, name)
                    if score is not None:
                        scores.append(score)
                        
                except Exception as e:
                    logger.error(f"Azure evaluator {name} failed: {e}")
                    results[name] = {"error": str(e)}
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            return {
                "success": True,
                "method": "azure_ai",
                "enabled": True,
                "average_score": avg_score,
                "total_evaluators": len(results),
                "successful_evaluators": len(scores),
                "results": results,
                "summary": self._generate_summary(results)
            }
            
        except Exception as e:
            logger.error(f"Azure evaluation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _simple_evaluation(self, response_text: str, user_query: str) -> Dict[str, Any]:
        """Simple fallback evaluation based on heuristics."""
        if not response_text:
            return {"enabled": False, "error": "No response text provided"}
        
        scores = {}
        
        # Simple intent evaluation
        if "intent" in self.metrics:
            scores["intent"] = self._evaluate_intent_simple(response_text, user_query)
        
        # Simple coherence evaluation
        if "coherence" in self.metrics:
            scores["coherence"] = self._evaluate_coherence_simple(response_text)
        
        # Simple tool usage evaluation
        if "tools" in self.metrics:
            scores["tools"] = self._evaluate_tools_simple(response_text)
        
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            "enabled": True,
            "method": "simple_fallback",
            "average_score": avg_score,
            "total_evaluators": len(scores),
            "successful_evaluators": len(scores),
            "results": scores,
            "summary": self._generate_simple_summary(scores)
        }
    
    def _evaluate_intent_simple(self, response_text: str, user_query: str) -> float:
        """Simple intent evaluation based on keywords."""
        if not user_query or not response_text:
            return 3.0
        
        # Check if response addresses key terms from the query
        query_words = set(user_query.lower().split())
        response_words = set(response_text.lower().split())
        
        # Common calendar-related keywords
        calendar_keywords = {"schedule", "event", "meeting", "book", "available", "room", "time", "date"}
        
        # Check keyword overlap
        common_words = query_words.intersection(response_words)
        calendar_context = bool(query_words.intersection(calendar_keywords))
        
        if len(common_words) >= 2 and calendar_context:
            return 4.5
        elif len(common_words) >= 1 and calendar_context:
            return 4.0
        elif calendar_context:
            return 3.5
        else:
            return 3.0
    
    def _evaluate_coherence_simple(self, response_text: str) -> float:
        """Simple coherence evaluation based on structure."""
        if not response_text:
            return 1.0
        
        score = 3.0  # Base score
        
        # Check for proper sentence structure
        sentences = response_text.split('.')
        if len(sentences) > 1:
            score += 0.5
        
        # Check for questions (indicates engagement)
        if '?' in response_text:
            score += 0.5
        
        # Check for structured lists or numbered items
        if any(marker in response_text for marker in ['1.', '2.', '•', '-', '*']):
            score += 0.5
        
        # Check for polite language
        polite_words = ['please', 'thank', 'help', 'assist', 'would', 'could']
        if any(word in response_text.lower() for word in polite_words):
            score += 0.5
        
        return min(score, 5.0)
    
    def _evaluate_tools_simple(self, response_text: str) -> float:
        """Simple tool usage evaluation."""
        # This is a simplified version - in a real system, you'd check actual tool calls
        tool_indicators = ['check', 'schedule', 'book', 'available', 'room', 'calendar']
        
        if any(indicator in response_text.lower() for indicator in tool_indicators):
            return 0.8  # 80% - good tool usage indicated
        else:
            return 0.6  # 60% - some tool usage
    
    def _extract_score(self, result: Dict[str, Any], evaluator_name: str) -> Optional[float]:
        """Extract numerical score from evaluator result."""
        if not isinstance(result, dict) or result.get("error"):
            return None
            
        try:
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
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting score for {evaluator_name}: {e}")
            return None
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate summary for Azure AI results."""
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
    
    def _generate_simple_summary(self, scores: Dict[str, float]) -> str:
        """Generate summary for simple evaluation results."""
        if not scores:
            return "No evaluation results"
        
        summary_parts = []
        
        for name, score in scores.items():
            if name == "intent":
                summary_parts.append(f"Intent: {score:.1f}/5")
            elif name == "coherence":
                summary_parts.append(f"Coherence: {score:.1f}/5")
            elif name == "tools":
                summary_parts.append(f"Tools: {score:.1%}")
        
        return " | ".join(summary_parts) if summary_parts else "No scores available"

# Global instance
_hybrid_evaluator = None

async def get_hybrid_evaluator(project_client):
    """Get or create the global hybrid evaluator instance."""
    global _hybrid_evaluator
    if _hybrid_evaluator is None:
        _hybrid_evaluator = HybridRealTimeEvaluator(project_client)
    return _hybrid_evaluator

async def quick_evaluate_response(project_client, thread_id: str, run_id: str, response_text: str = None, user_query: str = None) -> Dict[str, Any]:
    """
    Convenience function to quickly evaluate a response.
    
    Args:
        project_client: Azure AI project client
        thread_id: Thread ID of the conversation
        run_id: Run ID of the agent response
        response_text: The agent's response text (for fallback)
        user_query: The user's query (for fallback)
        
    Returns:
        Evaluation results dictionary
    """
    evaluator = await get_hybrid_evaluator(project_client)
    return await evaluator.evaluate_response(thread_id, run_id, response_text, user_query)

# Keep the original RealTimeEvaluator class for backward compatibility
RealTimeEvaluator = HybridRealTimeEvaluator
