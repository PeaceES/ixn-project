# Agent Evaluation Module

"""
Calendar Agent Evaluation Module

This module provides evaluation capabilities for the calendar scheduling agent
using simple heuristic-based evaluation. It includes:

- Agent response quality evaluation (coherence, intent resolution)
- Tool call accuracy assessment
- Basic content evaluation
- Real-time evaluation support

Usage:
    from evaluation.working_evaluator import WorkingRealTimeEvaluator, quick_evaluate_response
    
    evaluator = WorkingRealTimeEvaluator()
    results = await evaluator.evaluate_response(thread_id, run_id, response_text, user_query)
"""

from .working_evaluator import WorkingRealTimeEvaluator, quick_evaluate_response

__all__ = ['WorkingRealTimeEvaluator', 'quick_evaluate_response']
__version__ = '1.0.0'
