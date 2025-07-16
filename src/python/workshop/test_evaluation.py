#!/usr/bin/env python3
"""
Quick test script to verify the auto-evaluation system is working.
"""
import sys
import os
sys.path.insert(0, '.')

def test_real_time_evaluator():
    """Test the real-time evaluator"""
    print("🔍 Testing Real-Time Evaluator...")
    
    try:
        from evaluation.real_time_evaluator import RealTimeEvaluator
        
        # Create evaluator instance
        evaluator = RealTimeEvaluator()
        print(f"✅ Evaluator created successfully")
        print(f"📊 Enabled: {evaluator.enabled}")
        print(f"🔧 Metrics: {evaluator.metrics}")
        
        # Test evaluation
        if evaluator.enabled:
            test_response = "I'll schedule a meeting for next Tuesday at 2 PM as requested."
            test_query = "Schedule a meeting for next Tuesday at 2 PM"
            test_thread_id = "test_thread_123"
            test_run_id = "test_run_456"
            
            print("\n🔄 Testing evaluation...")
            result = evaluator.evaluate_response(
                response=test_response,
                user_query=test_query,
                thread_id=test_thread_id,
                run_id=test_run_id
            )
            
            print(f"✅ Test evaluation completed: {result}")
        else:
            print("⚠️ Auto-evaluation is disabled in .env")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_stream_handler_integration():
    """Test stream handler integration"""
    print("\n🔍 Testing Stream Handler Integration...")
    
    try:
        from agent.stream_event_handler import StreamEventHandler
        import inspect
        
        # Check if evaluator is imported
        source = inspect.getsource(StreamEventHandler)
        if 'RealTimeEvaluator' in source:
            print("✅ RealTimeEvaluator found in StreamEventHandler")
        else:
            print("❌ RealTimeEvaluator not found in StreamEventHandler")
            
        # Check if evaluation is called in on_done
        if 'evaluate_response' in source:
            print("✅ evaluate_response method found in StreamEventHandler")
        else:
            print("❌ evaluate_response method not found in StreamEventHandler")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing Environment Configuration...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        enable_eval = os.getenv('ENABLE_AUTO_EVALUATION', 'false').lower() == 'true'
        metrics = os.getenv('AUTO_EVAL_METRICS', 'intent,coherence,tools').split(',')
        
        print(f"📊 ENABLE_AUTO_EVALUATION: {enable_eval}")
        print(f"🔧 AUTO_EVAL_METRICS: {metrics}")
        
        if enable_eval:
            print("✅ Auto-evaluation is enabled")
        else:
            print("⚠️ Auto-evaluation is disabled")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Auto-Evaluation System Test")
    print("=" * 50)
    
    test_environment()
    test_real_time_evaluator()
    test_stream_handler_integration()
    
    print("\n✅ Test completed!")
