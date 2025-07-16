#!/usr/bin/env python3
"""
Simple test to verify evaluation setup
"""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

print("🔍 Testing evaluation system...")

# Test 1: Check environment variables
print("\n1. Environment Variables:")
print(f"   ENABLE_AUTO_EVALUATION: {os.getenv('ENABLE_AUTO_EVALUATION', 'Not Set')}")
print(f"   AUTO_EVAL_METRICS: {os.getenv('AUTO_EVAL_METRICS', 'Not Set')}")

# Test 2: Try importing modules
print("\n2. Module Imports:")
try:
    from evaluation.real_time_evaluator import RealTimeEvaluator
    print("   ✅ RealTimeEvaluator imported successfully")
except Exception as e:
    print(f"   ❌ RealTimeEvaluator import failed: {e}")

try:
    from agent.stream_event_handler import StreamEventHandler
    print("   ✅ StreamEventHandler imported successfully")
except Exception as e:
    print(f"   ❌ StreamEventHandler import failed: {e}")

# Test 3: Check if evaluator is properly configured
print("\n3. Evaluator Configuration:")
try:
    evaluator = RealTimeEvaluator()
    print(f"   Enabled: {evaluator.enabled}")
    print(f"   Metrics: {evaluator.metrics}")
    print("   ✅ Evaluator created successfully")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")

# Test 4: Test quick_evaluate_response import
print("\n4. Quick Evaluate Function:")
try:
    from evaluation.real_time_evaluator import quick_evaluate_response
    print("   ✅ quick_evaluate_response imported successfully")
except Exception as e:
    print(f"   ❌ quick_evaluate_response import failed: {e}")

print("\n✅ Test completed!")
