#!/usr/bin/env python3
"""
Simple test runner for the Calendar Agent Evaluator.

This script demonstrates how to use the agent evaluator to assess
the performance of the calendar scheduling agent.
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.agent_evaluator import CalendarAgentEvaluator

async def run_quick_evaluation():
    """Run a quick evaluation with a subset of test scenarios."""
    evaluator = CalendarAgentEvaluator()
    
    # Select a few key scenarios for quick testing
    quick_scenarios = [
        scenario for scenario in evaluator.test_scenarios
        if scenario["complexity"] in ["simple", "medium"]
    ][:3]  # Take first 3 scenarios
    
    print("Starting quick evaluation...")
    print(f"Selected {len(quick_scenarios)} scenarios:")
    for i, scenario in enumerate(quick_scenarios, 1):
        print(f"  {i}. {scenario['name']} ({scenario['complexity']})")
    
    # Run evaluation
    results = await evaluator.run_batch_evaluation(quick_scenarios)
    
    # Generate report
    report_path = await evaluator.generate_evaluation_report(
        results, 
        "quick_evaluation_report.json"
    )
    
    # Print results
    print("\n" + "="*60)
    print("QUICK EVALUATION RESULTS")
    print("="*60)
    print(f"Total Scenarios: {results['summary']['total_scenarios']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    
    if results['summary']['average_scores']:
        print("\nAverage Scores:")
        for evaluator_name, score in results['summary']['average_scores'].items():
            print(f"  {evaluator_name}: {score:.2f}")
    
    print(f"\nDetailed report saved to: {report_path}")
    
    return results

async def run_full_evaluation():
    """Run the full evaluation suite."""
    evaluator = CalendarAgentEvaluator()
    
    print("Starting full evaluation...")
    print(f"Total scenarios to evaluate: {len(evaluator.test_scenarios)}")
    
    # Run full evaluation
    results = await evaluator.run_batch_evaluation()
    
    # Generate report
    report_path = await evaluator.generate_evaluation_report(
        results, 
        "full_evaluation_report.json"
    )
    
    # Print results
    print("\n" + "="*60)
    print("FULL EVALUATION RESULTS")
    print("="*60)
    print(f"Total Scenarios: {results['summary']['total_scenarios']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    
    if results['summary']['average_scores']:
        print("\nAverage Scores:")
        for evaluator_name, score in results['summary']['average_scores'].items():
            print(f"  {evaluator_name}: {score:.2f}")
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Print recommendations
    if results.get('recommendations'):
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
    
    return results

async def main():
    """Main function with user choice."""
    print("Calendar Agent Evaluator")
    print("="*30)
    print("1. Quick Evaluation (3 scenarios)")
    print("2. Full Evaluation (all scenarios)")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                await run_quick_evaluation()
                break
            elif choice == "2":
                await run_full_evaluation()
                break
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
