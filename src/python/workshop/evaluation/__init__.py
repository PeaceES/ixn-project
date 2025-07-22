# Agent Evaluation Module

"""
Calendar Agent Evaluation Module

This module provides comprehensive evaluation capabilities for the calendar scheduling agent
using the Azure AI Evaluation SDK. It includes:

- Agent response quality evaluation (relevance, coherence, fluency)
- Content safety evaluation
- Groundedness evaluation
- Test scenario management
- Batch evaluation and reporting

Usage:
    from evaluation.agent_evaluator import CalendarAgentEvaluator
    
    evaluator = CalendarAgentEvaluator()
    results = await evaluator.run_quick_evaluation()
"""

from .agent_evaluator import CalendarAgentEvaluator

__all__ = ['CalendarAgentEvaluator']
__version__ = '1.0.0'
