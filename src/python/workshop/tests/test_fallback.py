#!/usr/bin/env python3
"""
Test the hybrid evaluator fallback functionality
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

def test_fallback_evaluation():
    """Test the fallback evaluation"""
    print("🔍 Testing Fallback Evaluation...")
    
    try:
        from evaluation.hybrid_evaluator import HybridRealTimeEvaluator
        
        # Create evaluator without project client (should use fallback)
        evaluator = HybridRealTimeEvaluator(project_client=None)
        print(f"✅ Evaluator created")
        print(f"📊 Enabled: {evaluator.enabled}")
        print(f"Metrics: {evaluator.metrics}")
        
        # Test fallback evaluation
        test_response = "Yes, there is one event scheduled for today, July 16th, 2025: Competition rehearsal from 10:00 AM - 12:00 PM in Main Lecture Hall organized by Alice Chen."
        test_query = "hi the date is 16th of july 2025, are there any events scheduled today?"
        
        print("\n🔄 Testing fallback evaluation...")
        result = evaluator._simple_evaluation(test_response, test_query)
        
        print(f"✅ Fallback evaluation result: {result}")
        print(f"📊 Enabled: {result.get('enabled')}")
        print(f"📊 Method: {result.get('method')}")
        print(f"📊 Average Score: {result.get('average_score')}")
        print(f"📊 Summary: {result.get('summary')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_evaluation()
