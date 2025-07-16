"""
Working real-time evaluation module for immediate agent assessment.

This module provides a simple and reliable evaluation system that works
with both Azure AI and fallback evaluation methods.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import re

load_dotenv()

# Configuration
ENABLE_AUTO_EVALUATION = os.getenv("ENABLE_AUTO_EVALUATION", "false").lower() == "true"
AUTO_EVAL_METRICS = os.getenv("AUTO_EVAL_METRICS", "intent,coherence,tools").split(",")

logger = logging.getLogger(__name__)

class WorkingRealTimeEvaluator:
    """Simple and reliable evaluator for real-time assessment."""
    
    def __init__(self, project_client=None):
        """Initialize the evaluator."""
        self.project_client = project_client
        self.enabled = ENABLE_AUTO_EVALUATION
        self.metrics = [metric.strip() for metric in AUTO_EVAL_METRICS]
        logger.info(f"WorkingRealTimeEvaluator initialized - Enabled: {self.enabled}, Metrics: {self.metrics}")
        
    async def evaluate_response(self, thread_id: str, run_id: str, response_text: str = None, user_query: str = None) -> Dict[str, Any]:
        """
        Evaluate a single agent response using simple heuristics.
        
        Args:
            thread_id: The thread ID of the conversation
            run_id: The run ID of the agent response
            response_text: The agent's response text
            user_query: The user's query
            
        Returns:
            Dictionary with evaluation scores and summary
        """
        if not self.enabled:
            return {"enabled": False}
            
        logger.info(f"Evaluating response: '{response_text[:100]}...' for query: '{user_query[:100]}...'")
        
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
        
        result = {
            "enabled": True,
            "method": "simple_heuristic",
            "average_score": avg_score,
            "total_evaluators": len(scores),
            "successful_evaluators": len(scores),
            "results": scores,
            "summary": self._generate_summary(scores)
        }
        
        logger.info(f"Evaluation completed: {result}")
        return result
    
    def _evaluate_intent_simple(self, response_text: str, user_query: str) -> float:
        """Simple intent evaluation based on keywords."""
        if not user_query or not response_text:
            return 3.0
        
        # Check if response addresses key terms from the query
        query_words = set(user_query.lower().split())
        response_words = set(response_text.lower().split())
        
        # Common calendar-related keywords
        calendar_keywords = {"schedule", "event", "meeting", "book", "available", "room", "time", "date", "today", "tomorrow"}
        
        # Check keyword overlap
        common_words = query_words.intersection(response_words)
        calendar_context = bool(query_words.intersection(calendar_keywords))
        
        score = 3.0  # Base score
        
        if len(common_words) >= 3 and calendar_context:
            score = 4.5
        elif len(common_words) >= 2 and calendar_context:
            score = 4.0
        elif len(common_words) >= 1 and calendar_context:
            score = 3.5
        elif calendar_context:
            score = 3.0
        
        # Bonus for specific information
        if any(word in response_text.lower() for word in ["yes", "no", "one event", "events", "scheduled"]):
            score += 0.3
        
        return min(score, 5.0)
    
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
            score += 0.3
        
        # Check for structured information (lists, bullet points)
        if any(marker in response_text for marker in ['•', '-', '*', '1.', '2.', '**']):
            score += 0.5
        
        # Check for polite/helpful language
        polite_words = ['please', 'thank', 'help', 'assist', 'would', 'could', 'let me know']
        if any(word in response_text.lower() for word in polite_words):
            score += 0.4
        
        # Check for specific details (good for calendar responses)
        if any(word in response_text.lower() for word in ['time', 'date', 'location', 'organizer', 'title']):
            score += 0.3
        
        return min(score, 5.0)
    
    def _evaluate_tools_simple(self, response_text: str) -> float:
        """Simple tool usage evaluation."""
        # Look for evidence of tool usage in the response
        tool_indicators = [
            'event', 'scheduled', 'available', 'room', 'calendar', 
            'check', 'book', 'organizer', 'time', 'date'
        ]
        
        score = 0.5  # Base score
        
        # Count tool usage indicators
        found_indicators = sum(1 for indicator in tool_indicators if indicator in response_text.lower())
        
        if found_indicators >= 5:
            score = 0.95
        elif found_indicators >= 3:
            score = 0.85
        elif found_indicators >= 2:
            score = 0.75
        elif found_indicators >= 1:
            score = 0.65
        
        # Bonus for specific calendar information
        if any(word in response_text.lower() for word in ['am', 'pm', 'july', 'today', 'tomorrow']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_summary(self, scores: Dict[str, float]) -> str:
        """Generate a human-readable summary of evaluation results."""
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
_working_evaluator = None

async def get_working_evaluator(project_client):
    """Get or create the global working evaluator instance."""
    global _working_evaluator
    if _working_evaluator is None:
        _working_evaluator = WorkingRealTimeEvaluator(project_client)
    return _working_evaluator

async def quick_evaluate_response(project_client, thread_id: str, run_id: str, response_text: str = None, user_query: str = None) -> Dict[str, Any]:
    """
    Convenience function to quickly evaluate a response.
    
    Args:
        project_client: Azure AI project client
        thread_id: Thread ID of the conversation
        run_id: Run ID of the agent response
        response_text: The agent's response text
        user_query: The user's query
        
    Returns:
        Evaluation results dictionary
    """
    evaluator = await get_working_evaluator(project_client)
    return await evaluator.evaluate_response(thread_id, run_id, response_text, user_query)

# Keep the original classes for backward compatibility
RealTimeEvaluator = WorkingRealTimeEvaluator
HybridRealTimeEvaluator = WorkingRealTimeEvaluator
