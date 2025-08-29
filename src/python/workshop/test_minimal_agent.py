#!/usr/bin/env python3
"""
Test script to reproduce the message role issue with minimal setup.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import MessageRole
from azure.identity import DefaultAzureCredential

load_dotenv()

async def test_minimal_agent():
    """Test with minimal agent setup to isolate the issue."""
    
    PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
    MODEL_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")
    
    print(f"🔍 Testing minimal agent with model: {MODEL_NAME}")
    
    try:
        # Initialize the client
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING,
        )
        
        # Create a very simple agent (no complex instructions or tools)
        agent = await project_client.agents.create_agent(
            model=MODEL_NAME,
            name="Minimal Test Agent",
            instructions="You are a helpful assistant. Keep responses short.",
            temperature=0.1,
        )
        
        print(f"✅ Created minimal agent: {agent.id}")
        
        # Create thread
        thread = await project_client.agents.create_thread()
        print(f"✅ Created thread: {thread.id}")
        
        # Send message
        message = await project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="hello"
        )
        print(f"✅ Created message: {message.id}")
        
        # Create run (non-streaming)
        run = await project_client.agents.create_run(
            thread_id=thread.id,
            agent_id=agent.id,
            temperature=0.1,
        )
        print(f"✅ Started run: {run.id}")
        
        # Wait for completion
        max_wait = 30
        wait_count = 0
        while wait_count < max_wait:
            run = await project_client.agents.get_run(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"📊 Run status: {run.status}")
            
            if run.status.value == "completed":
                break
            elif run.status.value in ["failed", "cancelled", "expired"]:
                print(f"❌ Run failed with status: {run.status}")
                if hasattr(run, 'last_error') and run.last_error:
                    print(f"❌ Error: {run.last_error}")
                return
                
            await asyncio.sleep(1)
            wait_count += 1
        
        if wait_count >= max_wait:
            print(f"⏰ Run timed out after {max_wait} seconds")
            return
            
        # Get messages
        messages = await project_client.agents.list_messages(thread_id=thread.id)
        
        print(f"\n📋 Messages in thread ({len(messages.data)} total):")
        for i, msg in enumerate(messages.data):
            role = getattr(msg, 'role', 'UNKNOWN')
            content = ""
            if hasattr(msg, 'content') and msg.content:
                for content_item in msg.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        if hasattr(content_item.text, 'value'):
                            content += content_item.text.value
                        else:
                            content += str(content_item.text)
            
            print(f"  {i+1}. ID: {msg.id}")
            print(f"     Role: {role}")
            print(f"     Content: {content[:100]}{'...' if len(content) > 100 else ''}")
            print()
        
        # Find the assistant's response
        assistant_response = None
        for msg in messages.data:
            role = getattr(msg, 'role', None)
            # Check for the correct role - Azure AI Agent Service uses MessageRole.AGENT for assistant responses
            if role and (str(role).lower() in ['assistant', 'agent'] or 
                        str(role) in ['MessageRole.ASSISTANT', 'MessageRole.AGENT'] or
                        role == MessageRole.AGENT):
                content = ""
                if hasattr(msg, 'content') and msg.content:
                    for content_item in msg.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            if hasattr(content_item.text, 'value'):
                                content += content_item.text.value
                            else:
                                content += str(content_item.text)
                if content.strip() and content.strip().lower() != "hello":
                    assistant_response = content
                    break
        
        if assistant_response:
            print(f"🎉 SUCCESS! Got assistant response: {assistant_response}")
        else:
            print("❌ No proper assistant response found")
            print("🔍 Analyzing message roles...")
            unique_roles = set()
            for msg in messages.data:
                role = getattr(msg, 'role', 'UNKNOWN')
                unique_roles.add(str(role))
            print(f"   Unique roles found: {unique_roles}")
        
        # Cleanup
        await project_client.agents.delete_thread(thread.id)
        await project_client.agents.delete_agent(agent.id)
        print("🗑️ Cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_agent())
