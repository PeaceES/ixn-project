"""
Agent Evaluator for Calendar Scheduling Agent

This module provides evaluation capabilities for the calendar scheduling agent
using the Azure AI Evaluation SDK. It evaluates agent performance across
multiple dimensions including intent resolution, tool call accuracy, task
adherence, and general quality metrics.
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Azure AI Evaluation SDK imports
from azure.ai.evaluation import (
    evaluate,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    ContentSafetyEvaluator
)
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration

# Azure AI Projects imports
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import ConnectionType

# Local imports - handle both direct execution and module imports
import sys
from pathlib import Path

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# New environment-driven configuration helpers
AZURE_OPENAI_ENDPOINT = (
    os.getenv("AZURE_OPENAI_ENDPOINT")
    or os.getenv("AOAI_ENDPOINT")
)
AZURE_OPENAI_API_KEY = (
    os.getenv("AZURE_OPENAI_API_KEY")
    or os.getenv("AOAI_API_KEY")
)
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

class CalendarAgentEvaluator:
    """
    Evaluator for the Calendar Scheduling Agent using Azure AI Evaluation SDK.
    
    This class provides comprehensive evaluation capabilities for agent performance
    including intent resolution, tool call accuracy, task adherence, and quality metrics.
    """
    
    def __init__(self):
        """Initialize the evaluator with Azure AI configuration."""
        # Import here to avoid circular import
        from agent_core import CalendarAgentCore
        from services.mcp_client import CalendarMCPClient
        from utils.utilities import Utilities
        self.agent_core = CalendarAgentCore()
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        print("[EVALUATOR] PROJECT_CONNECTION_STRING:", os.environ.get("PROJECT_CONNECTION_STRING"))
        print("[EVALUATOR] MODEL_DEPLOYMENT_NAME:", os.environ.get("MODEL_DEPLOYMENT_NAME"))
        
        # Test scenarios for evaluation
        self.test_scenarios = self._define_test_scenarios()
        
        # Initialize evaluators (will be set up when needed)
        self.evaluators = {}
    
    async def _initialize_evaluators(self) -> Dict[str, Any]:
        """Initialize all evaluators with proper model configuration."""
        try:
            # Ensure agent core is initialized
            if not self.agent_core.project_client:
                success, message = await self.agent_core.initialize_agent()
                if not success:
                    logger.error(f"Failed to initialize agent: {message}")
                    return {}
            
            # Validate required env vars for direct model config
            if not AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_ENDPOINT (or AOAI_ENDPOINT) not set")
            if not AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEY (or AOAI_API_KEY) not set")

            try:
                logger.info("Creating model configuration from environment variables...")
                model_config = AzureOpenAIModelConfiguration(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    azure_deployment=os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5-chat"),
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version=AZURE_OPENAI_API_VERSION,
                )
                logger.info("Successfully created model configuration for evaluators.")

                # Initialize quality evaluators with the model configuration
                quality_evaluators = {
                    "RelevanceEvaluator": RelevanceEvaluator(model_config=model_config),
                    "CoherenceEvaluator": CoherenceEvaluator(model_config=model_config),
                    "FluencyEvaluator": FluencyEvaluator(model_config=model_config),
                    "GroundednessEvaluator": GroundednessEvaluator(model_config=model_config)
                }
                
                # ContentSafetyEvaluator requires different parameters
                try:
                    # We need the project details for the ContentSafetyEvaluator
                    # The connection object doesn't directly expose this, so we parse the string once
                    connection_string = os.environ["PROJECT_CONNECTION_STRING"]
                    parts = connection_string.split(';')
                    subscription_id = parts[1]
                    resource_group = parts[2]
                    workspace_name = parts[3]

                    from azure.ai.projects.models import AzureAIProject
                    
                    # Create Azure AI project configuration for ContentSafetyEvaluator
                    azure_ai_project = AzureAIProject(
                        subscription_id=subscription_id,
                        resource_group_name=resource_group,
                        project_name=workspace_name
                    )
                    
                    quality_evaluators["ContentSafetyEvaluator"] = ContentSafetyEvaluator(
                        credential=DefaultAzureCredential(),
                        azure_ai_project=azure_ai_project
                    )
                    logger.info("Successfully initialized ContentSafetyEvaluator")
                    
                except Exception as e:
                    logger.warning(f"Could not initialize ContentSafetyEvaluator: {e}")
                    # Continue without it
                
                logger.info("Successfully initialized Azure AI evaluators with workspace-based configuration")
                return quality_evaluators
                
            except Exception as e:
                logger.error(f"Could not initialize Azure AI evaluators: {e}")
                raise Exception(f"Azure AI Evaluation SDK configuration failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize evaluators: {e}")
            raise Exception(f"Evaluator initialization failed: {e}")
    
    def _define_test_scenarios(self) -> List[Dict[str, Any]]:
        """Define test scenarios for evaluating the calendar agent."""
        return [
            {
                "name": "Basic Room Availability Check",
                "query": "Is the Main Conference Room available tomorrow at 2 PM?",
                "expected_tools": ["check_room_availability_via_mcp"],
                "expected_outcome": "availability_check",
                "complexity": "simple"
            },
            {
                "name": "List Available Rooms",
                "query": "Show me all available rooms for meetings",
                "expected_tools": ["get_rooms_via_mcp"],
                "expected_outcome": "room_list",
                "complexity": "simple"
            },
            {
                "name": "Schedule Meeting",
                "query": "Schedule a team meeting in the Alpha Meeting Room for tomorrow at 3 PM to 4 PM",
                "expected_tools": ["schedule_event_with_organizer"],
                "expected_outcome": "event_creation",
                "complexity": "medium"
            },
            {
                "name": "Check Current Events",
                "query": "What meetings are scheduled for today?",
                "expected_tools": ["get_events_via_mcp"],
                "expected_outcome": "event_list",
                "complexity": "simple"
            },
            {
                "name": "Complex Scheduling with Conflict Resolution",
                "query": "I need to book the Drama Studio for a 3-hour rehearsal next Friday, but if it's not available, suggest alternatives",
                "expected_tools": ["check_room_availability_via_mcp", "get_rooms_via_mcp"],
                "expected_outcome": "conflict_resolution",
                "complexity": "complex"
            },
            {
                "name": "Multi-step Planning",
                "query": "Help me plan a workshop for 20 people next week. I need a room with a projector and whiteboard",
                "expected_tools": ["get_rooms_via_mcp", "check_room_availability_via_mcp"],
                "expected_outcome": "planning_assistance",
                "complexity": "complex"
            }
        ]
    
    async def evaluate_agent_response(self, query: str, response: str, context: str = "") -> Dict[str, Any]:
        """
        Evaluate an agent response using Azure AI Evaluation SDK.
        
        Args:
            query: The user query/input to the agent
            response: The agent's response
            context: Additional context or ground truth information
            
        Returns:
            Dictionary containing evaluation results
        """
        try:
            # Initialize evaluators if not already done
            if not self.evaluators:
                self.evaluators = await self._initialize_evaluators()
            
            results = {}
            
            # Prepare evaluation data
            eval_data = {
                "query": query,
                "response": response,
                "context": context if context else "Calendar scheduling and room booking system",
                "ground_truth": context if context else "The agent should provide accurate calendar and room information"
            }
            
            # Run each evaluator
            for name, evaluator in self.evaluators.items():
                try:
                    if name == "ContentSafetyEvaluator":
                        # Content safety evaluator only needs query and response
                        result = evaluator(
                            query=query,
                            response=response
                        )
                    elif name == "GroundednessEvaluator":
                        # Groundedness evaluator needs context
                        result = evaluator(
                            query=query,
                            response=response,
                            context=eval_data["context"]
                        )
                    else:
                        # Other evaluators (Relevance, Coherence, Fluency)
                        result = evaluator(
                            query=query,
                            response=response
                        )
                    
                    results[name] = result
                    logger.info(f"✅ {name} completed successfully")
                    
                except Exception as e:
                    logger.error(f"❌ {name} failed: {e}")
                    results[name] = {"error": str(e)}
            
            return {
                "query": query,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "evaluation_results": results
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate agent response: {e}")
            return {"error": str(e)}
    
    async def run_test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test scenario and evaluate the agent's performance.
        
        Args:
            scenario: Test scenario configuration
            
        Returns:
            Dictionary containing scenario results and evaluation
        """
        logger.info(f"Running scenario: {scenario['name']}")
        
        try:
            # Initialize agent if not already done
            if not self.agent_core.agent:
                success, message = await self.agent_core.initialize_agent()
                if not success:
                    return {"error": f"Failed to initialize agent: {message}"}
            
            # Send the test query and get response
            success, response_text = await self.agent_core.process_message(
                scenario["query"]
            )
            
            if not success:
                return {"error": f"Agent processing failed: {response_text}"}
            
            # Create context for evaluation based on the scenario
            context = f"Scenario: {scenario['name']}. Expected outcome: {scenario['expected_outcome']}. Complexity: {scenario['complexity']}"
            
            # Evaluate the agent's response
            evaluation_results = await self.evaluate_agent_response(
                query=scenario["query"],
                response=response_text,
                context=context
            )
            
            return {
                "scenario": scenario,
                "evaluation": evaluation_results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to run scenario {scenario['name']}: {e}")
            return {
                "scenario": scenario,
                "error": str(e),
                "success": False
            }
    
    async def run_batch_evaluation(self, scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run batch evaluation on multiple scenarios.
        
        Args:
            scenarios: List of scenarios to evaluate (defaults to all test scenarios)
            
        Returns:
            Dictionary containing batch evaluation results
        """
        if scenarios is None:
            scenarios = self.test_scenarios
        
        logger.info(f"Running batch evaluation on {len(scenarios)} scenarios")
        
        batch_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_scenarios": len(scenarios),
            "results": [],
            "summary": {
                "successful": 0,
                "failed": 0,
                "average_scores": {}
            }
        }
        
        # Run each scenario
        for scenario in scenarios:
            result = await self.run_test_scenario(scenario)
            batch_results["results"].append(result)
            
            if result.get("success"):
                batch_results["summary"]["successful"] += 1
            else:
                batch_results["summary"]["failed"] += 1
        
        # Calculate average scores
        batch_results["summary"]["average_scores"] = self._calculate_average_scores(
            batch_results["results"]
        )
        
        return batch_results
    
    def _calculate_average_scores(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average scores across all successful evaluations."""
        score_totals = {}
        score_counts = {}
        
        for result in results:
            if not result.get("success"):
                continue
                
            evaluation = result.get("evaluation", {})
            eval_results = evaluation.get("evaluation_results", {})
            
            for evaluator_name, eval_result in eval_results.items():
                if isinstance(eval_result, dict) and not eval_result.get("error"):
                    # Extract numeric scores from different evaluator result formats
                    score = None
                    
                    # Common score field names in Azure AI Evaluation SDK
                    score_fields = [
                        "score", "relevance", "coherence", "fluency", 
                        "groundedness", "content_safety_score", "overall_score"
                    ]
                    
                    for field in score_fields:
                        if field in eval_result and isinstance(eval_result[field], (int, float)):
                            score = eval_result[field]
                            break
                    
                    # If no direct score, try to find any numeric value
                    if score is None:
                        for key, value in eval_result.items():
                            if isinstance(value, (int, float)) and 0 <= value <= 5:  # Assuming 0-5 scale
                                score = value
                                break
                    
                    if score is not None:
                        if evaluator_name not in score_totals:
                            score_totals[evaluator_name] = 0
                            score_counts[evaluator_name] = 0
                        score_totals[evaluator_name] += score
                        score_counts[evaluator_name] += 1
        
        # Calculate averages
        averages = {}
        for evaluator_name in score_totals:
            if score_counts[evaluator_name] > 0:
                averages[evaluator_name] = score_totals[evaluator_name] / score_counts[evaluator_name]
        
        return averages
    
    async def generate_evaluation_report(self, results: Dict[str, Any], output_file: str = "evaluation_report.json") -> str:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            results: Evaluation results from batch evaluation
            output_file: Output file name for the report
            
        Returns:
            Path to the generated report file
        """
        report_path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation", output_file)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Create enhanced report
        report = {
            "evaluation_metadata": {
                "timestamp": results.get("timestamp"),
                "total_scenarios": results.get("total_scenarios"),
                "evaluator_version": "azure-ai-evaluation-sdk",
                "agent_type": "calendar_scheduling_agent"
            },
            "summary": results.get("summary", {}),
            "detailed_results": results.get("results", []),
            "recommendations": self._generate_recommendations(results)
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Evaluation report saved to: {report_path}")
        return report_path
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        summary = results.get("summary", {})
        avg_scores = summary.get("average_scores", {})
        
        # Check for low-performing evaluators
        for evaluator, score in avg_scores.items():
            if score < 3.0:  # Assuming 1-5 scale
                recommendations.append(f"Consider improving {evaluator} performance (current score: {score:.2f})")
        
        # Check success rate
        total = summary.get("total_scenarios", 0)
        failed = summary.get("failed", 0)
        if total > 0 and (failed / total) > 0.2:  # More than 20% failure rate
            recommendations.append("High failure rate detected. Review agent initialization and error handling.")
        
        # Generic recommendations
        if not recommendations:
            recommendations.append("Overall performance is satisfactory. Continue monitoring and consider expanding test scenarios.")
        
        return recommendations
    
    async def evaluate_simple_query(self, query: str, expected_tools: List[str] = None) -> Dict[str, Any]:
        """
        Simple evaluation method for testing agent responses to individual queries.
        
        Args:
            query: The query to send to the agent
            expected_tools: List of expected tools that should be called (optional)
            
        Returns:
            Dictionary containing the query, response, and evaluation results
        """
        try:
            # Initialize agent if not already done
            if not self.agent_core.agent:
                success, message = await self.agent_core.initialize_agent()
                if not success:
                    return {"error": f"Failed to initialize agent: {message}"}
            
            logger.info(f"Evaluating query: {query}")
            
            # Send query to agent and get response
            success, response_text = await self.agent_core.process_message(
                query
            )
            
            if not success:
                return {"error": f"Agent processing failed: {response_text}"}
            
            # Evaluate the response
            evaluation_results = await self.evaluate_agent_response(
                query=query,
                response=response_text,
                context="Calendar and room booking assistant evaluation"
            )
            
            return {
                "query": query,
                "response": response_text,
                "evaluation": evaluation_results,
                "expected_tools": expected_tools,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate query '{query}': {e}")
            return {
                "query": query,
                "error": str(e),
                "success": False
            }

    async def run_quick_evaluation(self) -> Dict[str, Any]:
        """
        Run a quick evaluation with a few simple test cases.
        
        Returns:
            Dictionary containing quick evaluation results
        """
        quick_scenarios = [
            {
                "query": "What rooms are available for booking?",
                "expected_tools": ["get_rooms_via_mcp"]
            },
            {
                "query": "Is the Main Conference Room available tomorrow at 2 PM?",
                "expected_tools": ["check_room_availability_via_mcp"]
            },
            {
                "query": "Show me today's scheduled meetings",
                "expected_tools": ["get_events_via_mcp"]
            }
        ]
        
        logger.info("Running quick evaluation...")
        results = []
        
        for scenario in quick_scenarios:
            result = await self.evaluate_simple_query(
                query=scenario["query"],
                expected_tools=scenario.get("expected_tools")
            )
            results.append(result)
            
            # Small delay between queries
            await asyncio.sleep(2)
        
        # Calculate summary
        successful = sum(1 for r in results if r.get("success"))
        total = len(results)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_queries": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "results": results
        }

async def main():
    """Main function to demonstrate agent evaluation."""
    print("🚀 Starting Calendar Agent Evaluation")
    print("=" * 50)
    
    evaluator = CalendarAgentEvaluator()
    
    # First run a quick evaluation to test basic functionality
    print("\n⚡ Running Quick Evaluation...")
    quick_results = await evaluator.run_quick_evaluation()
    
    print(f"\n📊 Quick Evaluation Results:")
    print(f"   Success Rate: {quick_results['success_rate']:.1%}")
    print(f"   Successful: {quick_results['successful']}/{quick_results['total_queries']}")
    
    # Show individual results
    for i, result in enumerate(quick_results['results'], 1):
        status = "✅" if result.get('success') else "❌"
        print(f"   {status} Query {i}: {result['query'][:50]}...")
    
    # Ask user if they want to run full evaluation
    try:
        print(f"\n🔍 Run full batch evaluation? (y/n): ", end="")
        # For demo purposes, let's run a smaller batch
        print("y")  # Auto-answer for demo
        
        # Run batch evaluation on first 3 scenarios
        results = await evaluator.run_batch_evaluation(evaluator.test_scenarios[:3])
        
        # Generate report
        report_path = await evaluator.generate_evaluation_report(results)
        
        # Print summary
        print("\n" + "="*50)
        print("CALENDAR AGENT EVALUATION SUMMARY")
        print("="*50)
        print(f"Total Scenarios: {results['summary']['total_scenarios']}")
        print(f"Successful: {results['summary']['successful']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Report saved to: {report_path}")
        
        # Print average scores
        if results['summary']['average_scores']:
            print("\nAverage Scores:")
            for evaluator_name, score in results['summary']['average_scores'].items():
                print(f"  {evaluator_name}: {score:.2f}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation stopped by user")
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())