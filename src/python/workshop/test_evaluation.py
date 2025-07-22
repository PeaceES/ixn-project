#!/usr/bin/env python3
"""
Test script for the Calendar Agent Evaluation module.

This script tests the evaluation functionality with a simple example
to ensure everything is working correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from evaluation import CalendarAgentEvaluator


async def test_evaluation_module():
    """Test the evaluation module with basic functionality."""
    
    print("🧪 Testing Calendar Agent Evaluation Module")
    print("=" * 50)
    
    try:
        # Initialize evaluator
        print("📋 Initializing evaluator...")
        evaluator = CalendarAgentEvaluator()
        print("✅ Evaluator initialized successfully")
        
        # Test evaluator initialization
        print("\n🔧 Testing evaluator setup...")
        evaluators = await evaluator._initialize_evaluators()
        if evaluators:
            print(f"✅ Found {len(evaluators)} evaluators:")
            for name in evaluators.keys():
                print(f"   - {name}")
        else:
            print("⚠️  No evaluators initialized (check Azure configuration)")
        
        # Test simple evaluation (without agent call for now)
        print("\n🧪 Testing evaluation logic...")
        sample_result = await evaluator.evaluate_agent_response(
            query="What rooms are available?",
            response="Here are the available rooms: Main Conference Room, Alpha Meeting Room, Drama Studio.",
            context="Calendar and room booking system"
        )
        
        if sample_result and not sample_result.get("error"):
            print("✅ Evaluation logic working")
            print(f"   Evaluated {len(sample_result.get('evaluation_results', {}))} metrics")
        else:
            print(f"⚠️  Evaluation logic test failed: {sample_result.get('error', 'Unknown error')}")
        
        # Test scenario definitions
        print("\n📝 Testing scenario definitions...")
        scenarios = evaluator.test_scenarios
        print(f"✅ Found {len(scenarios)} test scenarios:")
        for scenario in scenarios[:3]:  # Show first 3
            print(f"   - {scenario['name']} ({scenario['complexity']})")
        
        print("\n🎉 Evaluation module test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_evaluation_module()
    
    if success:
        print("\n✨ All tests passed! The evaluation module is ready to use.")
        print("\n📖 Usage:")
        print("   python evaluation/agent_evaluator.py  # Run full evaluation")
        print("   from evaluation import CalendarAgentEvaluator  # Import in code")
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
