#!/usr/bin/env python3
"""Simple test for the working evaluator"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_working_evaluator():
    """Test the working evaluator synchronously"""
    print("🔍 Testing Working Evaluator...")
    
    try:
        from evaluation.working_evaluator import WorkingRealTimeEvaluator
        
        # Create evaluator
        evaluator = WorkingRealTimeEvaluator(project_client=None)
        print(f"✅ Evaluator created successfully")
        print(f"📊 Enabled: {evaluator.enabled}")
        print(f"🔧 Metrics: {evaluator.metrics}")
        
        # Test evaluation
        test_response = "Yes, there is one event scheduled for today, July 16th, 2025: Competition rehearsal from 10:00 AM - 12:00 PM in Main Lecture Hall organized by Alice Chen."
        test_query = "are there any events scheduled today?"
        
        print("\n🔄 Testing evaluation...")
        
        # Run async evaluation
        async def run_eval():
            return await evaluator.evaluate_response(
                thread_id="test_thread",
                run_id="test_run",
                response_text=test_response,
                user_query=test_query
            )
        
        result = asyncio.run(run_eval())
        
        print(f"✅ Evaluation completed:")
        print(f"  📊 Enabled: {result.get('enabled')}")
        print(f"  📊 Method: {result.get('method')}")
        print(f"  📊 Average Score: {result.get('average_score', 0):.2f}")
        print(f"  📊 Summary: {result.get('summary')}")
        print(f"  📊 Results: {result.get('results')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_working_evaluator()
    if success:
        print("\n✅ Working evaluator test passed!")
    else:
        print("\n❌ Working evaluator test failed!")
