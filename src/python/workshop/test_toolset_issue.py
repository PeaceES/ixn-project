#!/usr/bin/env python3
"""
Simple test to verify the specific issue with toolset configuration
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import AsyncFunctionTool, AsyncToolSet, CodeInterpreterTool

load_dotenv()

async def test_with_tools():
    """Test agent creation with tools to isolate the issue."""
    
    PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
    
    try:
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING,
        )
        
        print("🔍 Testing agent with different tool configurations...")
        
        # Test 1: Simple agent (no tools) - we know this works
        print("\n📋 Test 1: Simple agent (no tools)")
        agent1 = await project_client.agents.create_agent(
            model="gpt-5-chat",
            name="Test Agent - No Tools",
            instructions="You are a helpful assistant.",
            temperature=0.1,
        )
        print(f"✅ Simple agent works: {agent1.id}")
        
        # Test 2: Agent with just CodeInterpreter
        print("\n📋 Test 2: Agent with CodeInterpreter only")
        try:
            toolset2 = AsyncToolSet()
            toolset2.add(CodeInterpreterTool())
            
            agent2 = await project_client.agents.create_agent(
                model="gpt-5-chat",
                name="Test Agent - Code Interpreter",
                instructions="You are a helpful assistant with code interpreter.",
                temperature=0.1,
                toolset=toolset2,
            )
            print(f"✅ CodeInterpreter agent works: {agent2.id}")
        except Exception as e:
            print(f"❌ CodeInterpreter agent failed: {e}")
            agent2 = None
        
        # Test 3: Agent with empty function tool
        print("\n📋 Test 3: Agent with empty AsyncFunctionTool")
        try:
            toolset3 = AsyncToolSet()
            functions = AsyncFunctionTool([])  # Empty function list
            toolset3.add(functions)
            
            agent3 = await project_client.agents.create_agent(
                model="gpt-5-chat",
                name="Test Agent - Empty Functions",
                instructions="You are a helpful assistant.",
                temperature=0.1,
                toolset=toolset3,
            )
            print(f"✅ Empty functions agent works: {agent3.id}")
        except Exception as e:
            print(f"❌ Empty functions agent failed: {e}")
            agent3 = None
        
        # Test 4: Try a simple run with each working agent
        print("\n🔄 Testing simple runs...")
        
        for i, agent in enumerate([agent1, agent2, agent3], 1):
            if agent:
                try:
                    print(f"\n📋 Testing run for agent {i}: {agent.id}")
                    thread = await project_client.agents.create_thread()
                    await project_client.agents.create_message(thread_id=thread.id, role="user", content="hi")
                    
                    run = await project_client.agents.create_run(thread_id=thread.id, assistant_id=agent.id)
                    
                    # Poll for completion (simplified)
                    for _ in range(10):  # Max 10 checks
                        await asyncio.sleep(1)
                        run_status = await project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
                        if run_status.status.value in ['completed', 'failed', 'cancelled']:
                            break
                    
                    print(f"   Run status: {run_status.status.value}")
                    if run_status.status.value == "failed":
                        print(f"   Error: {run_status.last_error}")
                    
                    # Cleanup
                    await project_client.agents.delete_thread(thread.id)
                    
                except Exception as e:
                    print(f"   ❌ Run failed: {e}")
        
        # Cleanup agents
        try:
            await project_client.agents.delete_agent(agent1.id)
            if agent2:
                await project_client.agents.delete_agent(agent2.id)
            if agent3:
                await project_client.agents.delete_agent(agent3.id)
        except:
            pass
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_tools())
