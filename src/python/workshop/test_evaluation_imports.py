#!/usr/bin/env python3
"""
Simple test script to verify azure.ai.evaluation imports
"""

try:
    from azure.ai.evaluation import AIAgentConverter
    print("✅ AIAgentConverter imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AIAgentConverter: {e}")

try:
    from azure.ai.evaluation import IntentResolutionEvaluator
    print("✅ IntentResolutionEvaluator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import IntentResolutionEvaluator: {e}")

try:
    from azure.ai.evaluation import TaskAdherenceEvaluator
    print("✅ TaskAdherenceEvaluator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import TaskAdherenceEvaluator: {e}")

try:
    from azure.ai.evaluation import ToolCallAccuracyEvaluator
    print("✅ ToolCallAccuracyEvaluator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ToolCallAccuracyEvaluator: {e}")

try:
    from azure.ai.evaluation import evaluate
    print("✅ evaluate function imported successfully")
except ImportError as e:
    print(f"❌ Failed to import evaluate: {e}")

print("\nAll imports completed!")
