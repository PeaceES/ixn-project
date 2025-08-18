#!/usr/bin/env python3
"""
Simplified agent test that creates an agent without any tools to verify basic functionality.
"""

import asyncio
import logging
import os
import json
from dotenv import load_dotenv

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential
from utils.terminal_colors import TerminalColors as tc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Simple Test Agent"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
TEMPERATURE = 0.1

async def test_simple_agent():
    """Test basic agent functionality without any tools."""
    
    print(f"{tc.CYAN}Testing Simple Agent (No Tools)...{tc.RESET}")
    
    try:
        # Initialize project client
        print(f"{tc.YELLOW}Initializing project client...{tc.RESET}")
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING,
        )
        
        print(f"{tc.GREEN}✅ Project client initialized{tc.RESET}")
        
        # Create simple agent without tools
        print(f"{tc.YELLOW}Creating simple agent...{tc.RESET}")
        agent = await project_client.agents.create_agent(
            model=API_DEPLOYMENT_NAME,
            name=AGENT_NAME,
            instructions="You are a helpful assistant. Respond to user messages politely and helpfully. Keep your responses concise and friendly.",
            temperature=TEMPERATURE,
        )
        
        print(f"{tc.GREEN}✅ Agent created with ID: {agent.id}{tc.RESET}")
        
        # Create thread
        print(f"{tc.YELLOW}Creating thread...{tc.RESET}")
        thread = await project_client.agents.create_thread()
        
        print(f"{tc.GREEN}✅ Thread created with ID: {thread.id}{tc.RESET}")
        
        # Test basic queries
        test_queries = [
            "Hello",
            "Hi there!",
            "What can you help me with?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{tc.YELLOW}Test {i}: '{query}'{tc.RESET}")
            
            # Create message
            await project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query,
            )
            
            # Create and wait for run
            run = await project_client.agents.create_run(
                thread_id=thread.id,
                agent_id=agent.id,
                temperature=TEMPERATURE,
            )
            
            # Wait for completion
            await _wait_for_run_completion(project_client, thread.id, run.id)
            
            # Get messages
            messages = await project_client.agents.list_messages(thread_id=thread.id)
            
            # Find latest assistant message
            response_text = ""
            if hasattr(messages, 'data') and messages.data:
                for message in messages.data:
                    if getattr(message, 'role', None) == 'assistant':
                        content = getattr(message, 'content', [])
                        for content_item in content:
                            if hasattr(content_item, 'text') and content_item.text:
                                if hasattr(content_item.text, 'value'):
                                    response_text += content_item.text.value
                                else:
                                    response_text += str(content_item.text)
                        if response_text.strip():
                            break
            
            if response_text.strip():
                print(f"{tc.GREEN}✅ Test {i} PASSED: Got response{tc.RESET}")
                print(f"{tc.BLUE}Response: {response_text[:200]}...{tc.RESET}")
                
                # Test passed, now cleanup and return success
                print(f"{tc.YELLOW}Cleaning up...{tc.RESET}")
                await project_client.agents.delete_thread(thread.id)
                await project_client.agents.delete_agent(agent.id)
                print(f"{tc.GREEN}✅ Cleanup complete{tc.RESET}")
                return True
            else:
                print(f"{tc.RED}❌ Test {i} FAILED: No response{tc.RESET}")
                # Check run status for errors
                run_check = await project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
                status = getattr(run_check, 'status', None)
                last_error = getattr(run_check, 'last_error', None)
                print(f"{tc.RED}Run status: {status}, Error: {last_error}{tc.RESET}")
        
        # All tests failed, cleanup
        print(f"{tc.YELLOW}Cleaning up...{tc.RESET}")
        await project_client.agents.delete_thread(thread.id)
        await project_client.agents.delete_agent(agent.id)
        return False
        
    except Exception as e:
        print(f"{tc.RED}Test failed with exception: {e}{tc.RESET}")
        return False

async def _wait_for_run_completion(project_client, thread_id: str, run_id: str, max_wait: int = 30):
    """Wait for a run to complete."""
    for attempt in range(max_wait):
        try:
            run = await project_client.agents.get_run(
                thread_id=thread_id,
                run_id=run_id
            )
            status = getattr(run, 'status', None)
            
            if status in ['completed', 'failed', 'cancelled', 'expired']:
                print(f"Run finished with status: {status}")
                if status == 'failed':
                    last_error = getattr(run, 'last_error', None)
                    print(f"Run error: {last_error}")
                break
            
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error checking run status: {e}")
            break

if __name__ == "__main__":
    print(f"{tc.CYAN}Starting simple agent test...{tc.RESET}")
    result = asyncio.run(test_simple_agent())
    if result:
        print(f"{tc.GREEN}🎉 Simple agent test PASSED! Basic Azure AI connection works.{tc.RESET}")
    else:
        print(f"{tc.RED}💥 Simple agent test FAILED. There's a fundamental issue with Azure AI.{tc.RESET}")
