#!/usr/bin/env python3
"""
Test script for the simplified calendar agent (no tools version).
This tests basic agent initialization and message processing without tool complexity.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the current directory to path so we can import our agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_calendar_agent import SimpleCalendarAgentCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_simple_agent():
    """Test the simplified agent functionality."""
    print("="*60)
    print("Testing Simplified Calendar Agent (NO TOOLS)")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["PROJECT_CONNECTION_STRING", "MODEL_DEPLOYMENT_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    print(f"✅ Environment variables loaded")
    print(f"   MODEL_DEPLOYMENT_NAME: {os.getenv('MODEL_DEPLOYMENT_NAME')}")
    print(f"   PROJECT_CONNECTION_STRING: {os.getenv('PROJECT_CONNECTION_STRING')[:50]}...")
    
    agent_core = None
    try:
        # Initialize the simplified agent
        print(f"\n📋 Initializing simplified agent...")
        agent_core = SimpleCalendarAgentCore()
        
        success, message = await agent_core.initialize_agent()
        if not success:
            print(f"❌ Agent initialization failed: {message}")
            return False
        
        print(f"✅ Agent initialized successfully: {message}")
        
        # Test messages
        test_messages = [
            "Hello! Can you help me understand how calendar scheduling works?",
            "What are the best practices for scheduling meetings?",
            "I need to book a room for my team meeting next week. What should I consider?",
            "Thank you for your help!"
        ]
        
        print(f"\n💬 Testing message processing...")
        
        for i, test_message in enumerate(test_messages, 1):
            print(f"\n--- Test Message {i} ---")
            print(f"User: {test_message}")
            
            success, response = await agent_core.process_message(test_message)
            
            if success:
                print(f"✅ Agent: {response[:200]}{'...' if len(response) > 200 else ''}")
            else:
                print(f"❌ Error: {response}")
                return False
        
        # Test conversation history
        print(f"\n📜 Getting conversation history...")
        history = await agent_core.get_conversation_history()
        print(f"✅ Conversation has {len(history)} messages")
        
        for msg in history[-4:]:  # Show last 4 messages
            role = msg['role'].upper()
            content = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
            print(f"   {role}: {content}")
        
        print(f"\n🎉 All tests passed! Simplified agent is working correctly.")
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test failed with exception:")
        return False
        
    finally:
        if agent_core:
            try:
                await agent_core.cleanup()
                print(f"\n🧹 Agent cleaned up successfully")
            except Exception as e:
                print(f"\n⚠️ Cleanup error: {e}")

async def interactive_test():
    """Interactive test mode."""
    print("="*60)
    print("Interactive Simplified Calendar Agent Test")
    print("="*60)
    
    load_dotenv()
    agent_core = SimpleCalendarAgentCore()
    
    try:
        # Initialize agent
        print("Initializing agent...")
        success, message = await agent_core.initialize_agent()
        if not success:
            print(f"❌ Failed to initialize: {message}")
            return
        
        print(f"✅ {message}")
        print("\nYou can now chat with the simplified agent!")
        print("Type 'quit', 'exit', or press Ctrl+C to exit.")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                print("Agent is thinking...")
                success, response = await agent_core.process_message(user_input)
                
                if success:
                    print(f"Agent: {response}")
                else:
                    print(f"❌ Error: {response}")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Interactive test failed:")
    finally:
        await agent_core.cleanup()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_test())
    else:
        success = asyncio.run(test_simple_agent())
        sys.exit(0 if success else 1)
