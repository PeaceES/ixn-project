# Calendar Agent Evaluation

This directory contains the evaluation framework for the Calendar Scheduling Agent using the Azure AI Evaluation SDK.

## Overview

The evaluation system provides comprehensive assessment of the calendar agent's performance across multiple dimensions:

### Agent-Specific Evaluators
- **Intent Resolution**: Measures whether the agent correctly identifies the user's intent
- **Tool Call Accuracy**: Evaluates the correctness of function tool calls
- **Task Adherence**: Assesses whether the agent's responses adhere to assigned tasks

### General Quality Evaluators
- **Relevance**: Measures how relevant the response is to the user's query
- **Coherence**: Evaluates the logical flow and consistency of responses
- **Fluency**: Assesses the naturalness and readability of responses

## Files

- `agent_evaluator.py`: Main evaluation framework and CalendarAgentEvaluator class
- `run_evaluation.py`: Command-line interface for running evaluations
- `../data/evaluation/`: Directory where evaluation reports are saved

## Usage

### Prerequisites

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your Azure AI project is properly configured with environment variables:
```bash
export PROJECT_CONNECTION_STRING="your_project_connection_string"
export MODEL_DEPLOYMENT_NAME="your_model_deployment_name"
```

### Running Evaluations

#### Option 1: Using the Command Line Interface
```bash
python evaluation/run_evaluation.py
```

This will present you with options to run either a quick evaluation (3 scenarios) or a full evaluation (all scenarios).

#### Option 2: Using the Evaluator Directly
```python
from evaluation.agent_evaluator import CalendarAgentEvaluator

evaluator = CalendarAgentEvaluator()

# Run batch evaluation
results = await evaluator.run_batch_evaluation()

# Generate report
report_path = await evaluator.generate_evaluation_report(results)
```

#### Option 3: Evaluating a Single Conversation
```python
# If you have a specific thread_id and run_id
evaluation_results = await evaluator.evaluate_single_run(thread_id, run_id)
```

### Test Scenarios

The evaluation framework includes predefined test scenarios covering:

1. **Basic Room Availability Check** - Simple availability queries
2. **List Available Rooms** - Room listing functionality
3. **Schedule Meeting** - Event creation capabilities
4. **Check Current Events** - Event retrieval functionality
5. **Complex Scheduling with Conflict Resolution** - Advanced conflict handling
6. **Multi-step Planning** - Complex planning scenarios

### Evaluation Output

The evaluation system generates comprehensive reports including:

- **Summary Statistics**: Success/failure rates, average scores
- **Detailed Results**: Per-scenario evaluation results
- **Recommendations**: Actionable insights for improvement
- **Timestamps**: For tracking evaluation history

### Example Output

```json
{
  "evaluation_metadata": {
    "timestamp": "2025-01-15T10:30:00Z",
    "total_scenarios": 6,
    "evaluator_version": "azure-ai-evaluation-sdk",
    "agent_type": "calendar_scheduling_agent"
  },
  "summary": {
    "successful": 5,
    "failed": 1,
    "average_scores": {
      "IntentResolutionEvaluator": 4.2,
      "TaskAdherenceEvaluator": 4.5,
      "ToolCallAccuracyEvaluator": 0.85,
      "RelevanceEvaluator": 4.1,
      "CoherenceEvaluator": 4.3,
      "FluencyEvaluator": 4.4
    }
  },
  "recommendations": [
    "Consider improving ToolCallAccuracyEvaluator performance (current score: 0.85)",
    "Overall performance is satisfactory. Continue monitoring and consider expanding test scenarios."
  ]
}
```

## Understanding Evaluation Metrics

### Score Interpretation

- **Intent Resolution, Task Adherence, Relevance, Coherence, Fluency**: Likert scale 1-5 (higher is better)
- **Tool Call Accuracy**: Percentage 0-1 (higher is better)

### Thresholds

Each evaluator has configurable thresholds for pass/fail determination:
- Default threshold for 1-5 scale metrics: 3.0
- Default threshold for 0-1 scale metrics: 0.8

## Best Practices

1. **Regular Evaluation**: Run evaluations after significant changes to the agent
2. **Scenario Coverage**: Ensure test scenarios cover your agent's main use cases
3. **Trend Analysis**: Compare evaluation results over time to track improvements
4. **Error Analysis**: Review failed scenarios to identify improvement areas

## Troubleshooting

### Common Issues

1. **Evaluator Initialization Fails**
   - Check that your Azure AI project connection string is correct
   - Ensure the model deployment is available and accessible

2. **ToolCallAccuracyEvaluator Skipped**
   - This is normal if the agent run didn't involve tool calls
   - Ensure test scenarios trigger the expected tool functions

3. **High Failure Rate**
   - Check agent initialization in the main application
   - Verify that the MCP server is running and accessible

### Getting Help

For issues with the evaluation framework:
1. Check the Azure AI Evaluation SDK documentation
2. Review the agent logs for error details
3. Ensure all dependencies are properly installed

## Extension Points

The evaluation framework can be extended to:
- Add custom evaluators for domain-specific metrics
- Include safety evaluators for production deployments
- Implement automated regression testing
- Add performance benchmarking capabilities
