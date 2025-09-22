#!/usr/bin/env python3
"""
Simple script to check the last message from a shared thread.
This demonstrates how the communications agent can read messages from the scheduler agent.
"""

import asyncio
import os
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from utilities import Utilities

load_dotenv()

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
utilities = Utilities()

async def check_last_message(thread_id: str):
    """Simple function to check and display the last message from a thread."""
    if not thread_id:
        utilities.log_msg_purple("Error: No thread ID provided!")
        utilities.log_msg_purple("Usage: Set the THREAD_ID variable to your shared thread ID")
        return
    
    async with AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    ) as project_client:
        
        utilities.log_msg_green(f"Checking messages in thread: {thread_id}")
        
        try:
            # Get the last message
            messages = await project_client.agents.list_messages(thread_id=thread_id, limit=1)
            
            if messages.data:
                last_message = messages.data[0]
                
                utilities.log_msg_green("✅ Last message found!")
                utilities.log_msg_purple(f"Message ID: {last_message.id}")
                utilities.log_msg_purple(f"Role: {last_message.role}")
                utilities.log_msg_purple(f"Created: {last_message.created_at}")
                
                if last_message.content:
                    utilities.log_msg_green("Message Content:")
                    for content_item in last_message.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            utilities.log_msg_green(f"📝 {content_item.text.value}")
                
                # Check if this was from the scheduler agent
                if last_message.role == "assistant":
                    utilities.log_msg_green("🤖 This message appears to be from the scheduler agent")
                elif last_message.role == "user":
                    utilities.log_msg_purple("👤 This message appears to be from a user")
                
                return last_message
            else:
                utilities.log_msg_purple("❌ No messages found in the thread")
                return None
                
        except Exception as e:
            utilities.log_msg_purple(f"❌ Error reading messages: {str(e)}")
            return None

async def main():
    """Main function to check the last message."""
    # Set this to your shared thread ID between scheduler and comms agents
    THREAD_ID = None  # Replace with actual thread ID like "thread_abc123"
    
    # Alternative: Get from environment variable
    if not THREAD_ID:
        THREAD_ID = os.getenv("SHARED_THREAD_ID")
    
    if THREAD_ID:
        await check_last_message(THREAD_ID)
    else:
        utilities.log_msg_purple("Please set the THREAD_ID variable or SHARED_THREAD_ID environment variable")
        utilities.log_msg_purple("Example: THREAD_ID = 'thread_abc123xyz'")

if __name__ == "__main__":
    asyncio.run(main())
