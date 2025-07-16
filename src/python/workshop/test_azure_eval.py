#!/usr/bin/env python3
"""
Quick test script to test just the evaluation without the full agent interaction
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

async def test_azure_evaluator():
    """Test Azure AI evaluator initialization"""
    print("🔍 Testing Azure AI Evaluator...")
    
    try:
        # Initialize project client
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.getenv("PROJECT_CONNECTION_STRING"),
        )
        
        async with project_client:
            from evaluation.real_time_evaluator import RealTimeEvaluator
            
            # Create evaluator
            evaluator = RealTimeEvaluator(project_client)
            print(f"✅ Evaluator created with project client")
            print(f"📊 Enabled: {evaluator.enabled}")
            print(f"🔧 Metrics: {evaluator.metrics}")
            
            # Test initialization
            print("\n🔧 Testing evaluator initialization...")
            await evaluator._initialize_evaluators()
            
            print(f"✅ Initialization completed")
            print(f"📊 Initialized: {evaluator.initialized}")
            print(f"🔧 Evaluators: {list(evaluator.evaluators.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_azure_evaluator())
