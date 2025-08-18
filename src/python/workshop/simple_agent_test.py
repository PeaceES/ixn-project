#!/usr/bin/env python3
"""
Simple agent test without complex tools to isolate the core issue.
"""

import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
AGENT_NAME = "Simple Calendar Agent"
TEMPERATURE = 0.1

print(f"[SIMPLE] PROJECT_CONNECTION_STRING: {PROJECT_CONNECTION_STRING}")
print(f"[SIMPLE] MODEL_DEPLOYMENT_NAME: {API_DEPLOYMENT_NAME}")

async def test_simple_agent():
    """Test a very basic agent without tools."""
    try:
        # Parse connection string
        parts = PROJECT_CONNECTION_STRING.split(';')
        if len(parts) != 4:
            print(f"Invalid connection string format. Expected 4 parts, got {len(parts)}")
            return False
        
        print(f"[SIMPLE] Parsed connection string successfully")
        
        # Initialize AIProjectClient
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING,
        )
        print(f"[SIMPLE] Project client initialized")
        
        # Create simple agent without tools
        simple_instructions = """You are a helpful calendar scheduling assistant. 
        You can help users with general calendar-related questions and provide information.
        Be friendly and helpful in your responses."""
        
        agent = await project_client.agents.create_agent(
            model=API_DEPLOYMENT_NAME,
            name=AGENT_NAME,
            instructions=simple_instructions,
            temperature=TEMPERATURE,
        )
        print(f"[SIMPLE] Created agent with ID: {agent.id}")
        
        # Create thread
        thread = await project_client.agents.create_thread()
        print(f"[SIMPLE] Created thread with ID: {thread.id}")
        
        # Test basic conversation
        test_messages = [
            "Hello! Can you help me?",
            "What can you do?",
            "How are you today?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n[SIMPLE] Test {i}: Sending message: '{message}'")
            
            # Create message
            await project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=message,
            )
            
            # Create run
            run = await project_client.agents.create_run(
                thread_id=thread.id,
                agent_id=agent.id,
                temperature=TEMPERATURE,
            )
            
            print(f"[SIMPLE] Created run with ID: {run.id}")
            
            # Wait for completion
            max_wait = 30
            for attempt in range(max_wait):
                current_run = await project_client.agents.get_run(
                    thread_id=thread.id,
                    run_id=run.id
                )
                status = getattr(current_run, 'status', None)
                print(f"[SIMPLE] Run status: {status}")
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    break
                    
                await asyncio.sleep(1)
            
            # Get the response
            try:
                thread_messages = await project_client.agents.list_messages(thread_id=thread.id)
                response_found = False
                
                if hasattr(thread_messages, 'data'):
                    messages = thread_messages.data
                else:
                    messages = []
                    async for msg in thread_messages:
                        messages.append(msg)
                
                # Look for the latest assistant message
                for msg in messages:
                    if getattr(msg, 'role', None) == 'assistant':
                        content = getattr(msg, 'content', [])
                        response_text = ""
                        for content_item in content:
                            if hasattr(content_item, 'text') and content_item.text:
                                if hasattr(content_item.text, 'value'):
                                    response_text += content_item.text.value
                                else:
                                    response_text += str(content_item.text)
                        
                        if response_text.strip():
                            print(f"[SIMPLE] ✅ Got response: {response_text[:100]}...")
                            response_found = True
                            break
                
                if not response_found:
                    print(f"[SIMPLE] ❌ No response found for test {i}")
                    
                    # Check run status for errors
                    if status == 'failed':
                        last_error = getattr(current_run, 'last_error', {})
                        print(f"[SIMPLE] Run failed with error: {last_error}")
                    
                    return False
                    
            except Exception as e:
                print(f"[SIMPLE] Error getting response: {e}")
                return False
        
        print(f"\n[SIMPLE] 🎉 All tests passed! Basic agent functionality is working.")
        
        # Cleanup
        try:
            await project_client.agents.delete_thread(thread.id)
            await project_client.agents.delete_agent(agent.id)
            print(f"[SIMPLE] Cleaned up resources")
        except Exception as e:
            print(f"[SIMPLE] Cleanup warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"[SIMPLE] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("[SIMPLE] Starting simple agent test...")
    result = asyncio.run(test_simple_agent())
    if result:
        print("[SIMPLE] ✅ Simple agent test PASSED!")
    else:
        print("[SIMPLE] ❌ Simple agent test FAILED!")
