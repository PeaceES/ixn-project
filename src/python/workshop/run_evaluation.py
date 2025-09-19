#!/usr/bin/env python3
"""
Standalone Calendar Agent Evaluation Runner

This script safely runs the agent evaluator without modifying any existing code.
It will help identify any function name mismatches or data issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the workshop directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src/python/workshop"))

async def main():
    """Run calendar agent evaluation safely."""
    print("🔍 Calendar Agent Evaluation Runner")
    print("=" * 50)
    
    try:
        # Import and initialize evaluator
        print("📦 Importing evaluator...")
        from evaluation.agent_evaluator import CalendarAgentEvaluator
        
        print("🚀 Initializing evaluator...")
        evaluator = CalendarAgentEvaluator()
        
        # Test basic functionality first
        print("\n⚡ Testing basic agent functionality...")
        test_result = await evaluator.evaluate_simple_query(
            "What rooms are available?",
            expected_tools=["get_rooms_via_mcp"]
        )
        
        if test_result.get('success'):
            print("✅ Basic test passed!")
            print(f"   Query: {test_result['query']}")
            print(f"   Response: {test_result['response'][:100]}...")
        else:
            print("❌ Basic test failed:")
            print(f"   Error: {test_result.get('error', 'Unknown error')}")
            return
        
        # Ask user what to run
        print(f"\nWhat would you like to run?")
        print("1. Quick evaluation (3 simple queries)")
        print("2. Full batch evaluation (all scenarios)")
        print("3. Single custom query")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n⚡ Running quick evaluation...")
            results = await evaluator.run_quick_evaluation()
            
            print(f"\n📊 Quick Results:")
            print(f"   Success Rate: {results['success_rate']:.1%}")
            print(f"   Total Queries: {results['total_queries']}")
            
            for i, result in enumerate(results['results'], 1):
                status = "✅" if result.get('success') else "❌"
                print(f"   {status} Query {i}: {result.get('error', 'Success')}")
        
        elif choice == "2":
            print("\n🔍 Running full batch evaluation...")
            results = await evaluator.run_batch_evaluation()
            
            # Generate report
            report_path = await evaluator.generate_evaluation_report(results)
            
            print(f"\n📊 Batch Results:")
            print(f"   Total Scenarios: {results['summary']['total_scenarios']}")
            print(f"   Successful: {results['summary']['successful']}")
            print(f"   Failed: {results['summary']['failed']}")
            print(f"   Report: {report_path}")
            
        elif choice == "3":
            query = input("\nEnter your query: ").strip()
            if query:
                print(f"\n🔍 Evaluating: {query}")
                result = await evaluator.evaluate_simple_query(query)
                
                if result.get('success'):
                    print("✅ Query successful!")
                    print(f"Response: {result['response']}")
                else:
                    print("❌ Query failed:")
                    print(f"Error: {result.get('error')}")
        
        else:
            print("👋 Goodbye!")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and all dependencies are installed")
    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        print("💡 This might indicate function name changes or missing data")
        
        # Try to provide helpful debugging info
        print(f"\nDebugging info:")
        print(f"  Current directory: {os.getcwd()}")
        print(f"  Python path: {sys.path[:2]}...")

if __name__ == "__main__":
    asyncio.run(main())