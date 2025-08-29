"""
Simplified Calendar Agent Core - NO TOOLS VERSION
This is a testing version that removes all tool dependencies to test basic agent functionality.
"""

import asyncio
import logging
import os
from typing import Optional, Tuple
from dotenv import load_dotenv

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import MessageRole
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
AGENT_NAME = "Simple Calendar Assistant"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
TEMPERATURE = 0.1

# Simple instructions for a tool-less agent
SIMPLE_INSTRUCTIONS = """
You are a helpful calendar scheduling assistant. 

Since you don't have access to calendar tools in this simplified version, you can:
- Help users think through scheduling needs
- Suggest optimal meeting times based on general business practices
- Provide guidance on room booking procedures
- Answer general questions about calendar management

Always be helpful and acknowledge when you cannot perform actual calendar operations due to this being a test version.
"""

class SimpleCalendarAgentCore:
    """Simplified calendar agent for testing without tools."""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self.thread: Optional[AgentThread] = None
        self.project_client: Optional[AIProjectClient] = None
        self._operation_active = False

    async def cleanup(self):
        """Clean up resources."""
        self.agent = None
        self.thread = None
        if self.project_client:
            await self.project_client.close()

    def _cleanup_run_thread(self):
        """Reset agent and thread state after operation or error."""
        self.agent = None
        self.thread = None
        self._operation_active = False

    async def initialize_agent(self) -> Tuple[bool, str]:
        """Initialize the simplified agent. Returns (success, message)."""
        logger.info("[SimpleAgent] Initializing simplified agent...")
        
        # Cleanup any previous state
        self._cleanup_run_thread()

        try:
            # Parse connection string format: host;subscription_id;resource_group_name;project_name
            parts = PROJECT_CONNECTION_STRING.split(';')
            if len(parts) != 4:
                return False, f"Invalid PROJECT_CONNECTION_STRING format. Expected 4 parts, got {len(parts)}"
            
            host = parts[0]
            subscription_id = parts[1]
            resource_group_name = parts[2]
            project_name = parts[3]
            
            logger.info(f"[SimpleAgent] Connection details:")
            logger.info(f"[SimpleAgent]   Host: {host}")
            logger.info(f"[SimpleAgent]   Subscription: {subscription_id}")
            logger.info(f"[SimpleAgent]   Resource Group: {resource_group_name}")
            logger.info(f"[SimpleAgent]   Project: {project_name}")

            # Initialize AIProjectClient using hub-based connection string
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=PROJECT_CONNECTION_STRING,
            )

            # Create agent WITHOUT any tools
            self.agent = await self.project_client.agents.create_agent(
                model=API_DEPLOYMENT_NAME,
                name=AGENT_NAME,
                instructions=SIMPLE_INSTRUCTIONS,
                temperature=TEMPERATURE,
            )
            logger.info(f"[SimpleAgent] Created agent with ID: {self.agent.id}")

            # Create thread
            self.thread = await self.project_client.agents.create_thread()
            logger.info(f"[SimpleAgent] Created thread with ID: {self.thread.id}")

            success_msg = f"Simple agent initialized successfully (NO TOOLS)"
            logger.info(f"[SimpleAgent] Initialization complete. Agent ID: {self.agent.id}, Thread ID: {self.thread.id}")
            return True, success_msg
            
        except Exception as e:
            self._cleanup_run_thread()
            error_msg = f"Failed to initialize simple agent: {str(e)}"
            logger.error(f"[SimpleAgent] Initialization error: {error_msg}")
            return False, error_msg

    async def process_message(self, user_message: str) -> Tuple[bool, str]:
        """Process a message with the simplified agent. Returns (success, response)."""
        if not self.agent or not self.thread:
            logger.warning("[SimpleAgent] Agent or thread not initialized.")
            return False, "Agent not initialized"
            
        if self._operation_active:
            logger.warning("[SimpleAgent] Agent is busy processing another request.")
            return False, "Agent is busy processing another request. Please wait."
            
        self._operation_active = True
        logger.info(f"[SimpleAgent] Processing message: '{user_message[:50]}...'")
        
        try:
            # Create message
            await self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=user_message,
            )
            logger.info(f"[SimpleAgent] Message created for thread ID: {self.thread.id}")

            # Create run (no tools means no tool calls to handle)
            run = await self.project_client.agents.create_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                temperature=TEMPERATURE,
            )
            logger.info(f"[SimpleAgent] Run created with ID: {run.id}")
            
            # Wait for run to complete
            max_wait_time = 30
            wait_interval = 1
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # Get updated run status
                current_run = await self.project_client.agents.get_run(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
                
                logger.info(f"[SimpleAgent] Run status: {current_run.status}")
                
                if current_run.status == 'completed':
                    break
                elif current_run.status in ['failed', 'cancelled', 'expired']:
                    error_msg = f"Run failed with status: {current_run.status}"
                    if hasattr(current_run, 'last_error') and current_run.last_error:
                        error_msg += f" - {current_run.last_error}"
                    logger.error(f"[SimpleAgent] {error_msg}")
                    return False, error_msg
                elif current_run.status == 'requires_action':
                    # This shouldn't happen with no tools, but just in case
                    logger.warning("[SimpleAgent] Run requires action but no tools are configured")
                    return False, "Unexpected: Run requires action but no tools are available"
            
            if elapsed_time >= max_wait_time:
                logger.warning(f"[SimpleAgent] Run timed out after {max_wait_time} seconds")
                return False, "Agent response timed out"

            # Get the latest assistant message
            thread_messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
            response_text = ""
            
            if hasattr(thread_messages, 'data') and thread_messages.data:
                # Look for the most recent assistant message
                for message in thread_messages.data:
                    message_role = getattr(message, 'role', None)
                    
                    # Check for assistant/agent role
                    if (str(message_role) in ['assistant', 'agent'] or 
                        str(message_role).endswith('AGENT') or 
                        str(message_role).endswith('ASSISTANT') or
                        message_role == MessageRole.AGENT):
                        
                        content = getattr(message, 'content', None)
                        if content:
                            # Handle different content formats
                            if isinstance(content, list) and len(content) > 0:
                                # Content is a list of content parts
                                for part in content:
                                    if hasattr(part, 'text') and hasattr(part.text, 'value'):
                                        response_text = part.text.value
                                        break
                                    elif hasattr(part, 'text') and isinstance(part.text, str):
                                        response_text = part.text
                                        break
                            elif isinstance(content, str):
                                response_text = content
                            elif hasattr(content, 'text'):
                                if hasattr(content.text, 'value'):
                                    response_text = content.text.value
                                else:
                                    response_text = str(content.text)
                        
                        if response_text.strip():
                            break
            
            if not response_text.strip():
                logger.warning("[SimpleAgent] No assistant response found in thread messages")
                response_text = "I processed your message but couldn't retrieve the response. Please try again."
            
            logger.info(f"[SimpleAgent] Retrieved response: '{response_text[:100]}...'")
            return True, response_text.strip()
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"[SimpleAgent] Error processing message: {error_msg}")
            return False, error_msg
            
        finally:
            self._operation_active = False
            logger.info("[SimpleAgent] Operation complete")

    async def get_conversation_history(self) -> list:
        """Get conversation history from the current thread."""
        if not self.thread:
            return []
        
        try:
            messages = await self.project_client.agents.list_messages(thread_id=self.thread.id)
            history = []
            
            if hasattr(messages, 'data'):
                for message in reversed(messages.data):  # Reverse to get chronological order
                    role = str(getattr(message, 'role', 'unknown'))
                    content = getattr(message, 'content', '')
                    
                    # Extract text from content
                    if isinstance(content, list) and len(content) > 0:
                        for part in content:
                            if hasattr(part, 'text'):
                                if hasattr(part.text, 'value'):
                                    content = part.text.value
                                else:
                                    content = str(part.text)
                                break
                    elif hasattr(content, 'text'):
                        if hasattr(content.text, 'value'):
                            content = content.text.value
                        else:
                            content = str(content.text)
                    
                    history.append({
                        'role': role,
                        'content': str(content)
                    })
            
            return history
        except Exception as e:
            logger.error(f"[SimpleAgent] Error getting conversation history: {e}")
            return []
