"""
Streamlit UI for the Calendar Scheduling Agent.
This provides a web interface for testing and interacting with the agent.
"""

import streamlit as st
import asyncio
import json
import logging
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any

from agent_core import CalendarAgentCore

# Configure logging
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Calendar Scheduling Agent",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #dc3545;
        font-weight: bold;
    }
    .status-unreachable {
        color: #ffc107;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .quick-action-button {
        margin: 0.25rem;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        background-color: #2196f3;
        color: white;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    """Get or create the agent instance."""
    return CalendarAgentCore()

def run_async_in_streamlit(coroutine):
    """
    Run an async function in a way compatible with Streamlit.
    
    Streamlit runs in its own event loop, so we need to run async functions
    in a separate thread with their own event loop to avoid conflicts.
    
    Note: This is where the "Event loop is closed" error occurs due to
    cleanup timing issues between Streamlit and Azure SDK HTTP connections.
    """
    try:
        def run_with_asyncio():
            return asyncio.run(coroutine)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_with_asyncio)
            return future.result(timeout=120)  # 2 minute timeout
            
    except Exception as e:
        logger.error(f"Error in run_async_in_streamlit: {e}")
        st.error(f"Error running async operation: {e}")
        raise

def format_status_badge(status: str) -> str:
    """Format status as colored badge."""
    if status == "healthy":
        return f'<span class="status-healthy">🟢 {status.upper()}</span>'
    elif status == "unhealthy":
        return f'<span class="status-unhealthy">🔴 {status.upper()}</span>'
    else:
        return f'<span class="status-unreachable">🟡 {status.upper()}</span>'

def display_sidebar_status(agent_status: Dict[str, Any]):
    """Display agent status in sidebar."""
    st.sidebar.markdown("## Agent Status")
    
    # Agent initialization status
    if agent_status.get("agent_initialized"):
        st.sidebar.success("✅ Agent Initialized")
        st.sidebar.text(f"Agent ID: {agent_status.get('agent_id', 'N/A')[:8]}...")
        st.sidebar.text(f"Thread ID: {agent_status.get('thread_id', 'N/A')[:8]}...")
    else:
        st.sidebar.error("❌ Agent Not Initialized")
    
    # MCP Server status
    st.sidebar.markdown("### MCP Server")
    mcp_status = agent_status.get("mcp_status", "unknown")
    st.sidebar.markdown(format_status_badge(mcp_status), unsafe_allow_html=True)
    
    # User Directory status
    st.sidebar.markdown("### User Directory")
    user_dir = agent_status.get("user_directory", {})
    if user_dir.get("loaded"):
        st.sidebar.success(f"✅ Loaded ({user_dir.get('count', 0)} entries)")
    else:
        st.sidebar.warning("⚠️ Not loaded or empty")

def display_quick_actions():
    """Display quick action buttons."""
    st.sidebar.markdown("## ⚡ Quick Actions")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("List Rooms", key="list_rooms"):
            st.session_state.quick_query = "Show me all available rooms"
        if st.button("Today's Events", key="today_events"):
            st.session_state.quick_query = "What events are scheduled for today?"
    
    with col2:
        if st.button("Check Availability", key="check_availability"):
            st.session_state.quick_query = "Check if the Main Conference Room is available tomorrow at 2pm"
        if st.button("Schedule Meeting", key="schedule_meeting"):
            st.session_state.quick_query = "Schedule a meeting in the Alpha Meeting Room for tomorrow at 3pm"

def display_example_queries():
    """Display example queries."""
    st.sidebar.markdown("## Example Queries")
    
    examples = [
        "Show me all available rooms",
        "Check if the Main Conference Room is available tomorrow at 2pm",
        "Schedule a meeting in the Alpha Meeting Room for tomorrow at 3pm",
        "I want to book the Drama Studio for a rehearsal next Friday",
        "What events are scheduled for this week?",
        "Cancel my meeting in room 101 tomorrow",
        "Find a large conference room for 20 people next Monday"
    ]
    
    for i, example in enumerate(examples):
        if st.sidebar.button(f"{example[:30]}...", key=f"example_{i}"):
            st.session_state.quick_query = example

def initialize_agent_async():
    """Initialize the agent asynchronously."""
    agent = get_agent()
    success, message = run_async_in_streamlit(agent.initialize_agent())
    return success, message

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">Calendar Scheduling Agent</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'quick_query' not in st.session_state:
        st.session_state.quick_query = None
    
    # Get agent instance
    agent = get_agent()
    
    # Initialize agent if not already done
    if not st.session_state.agent_initialized:
        with st.spinner("Initializing Calendar Agent..."):
            success, message = initialize_agent_async()
            
            if success:
                st.session_state.agent_initialized = True
                st.success(f"✅ {message}")
                
                # Add welcome message
                welcome_msg = """
                 **Welcome to the Calendar Scheduling Agent!**
                
                I can help you with:
                - Listing available rooms
                - Checking room availability
                - Scheduling meetings and events
                - Viewing current events
                - Managing your calendar
                
                Try asking me something like "Show me all available rooms" or use the quick actions in the sidebar!
                """
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now()
                })
            else:
                st.error(f"{message}")
                st.stop()
    
    # Get current agent status
    if st.session_state.agent_initialized:
        agent_status = run_async_in_streamlit(agent.get_agent_status())
        display_sidebar_status(agent_status)
        display_quick_actions()
        display_example_queries()
    
    # Main chat interface
    st.markdown("## Chat with Agent")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "timestamp" in message:
                    st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
    
    # Handle quick query from sidebar
    if st.session_state.quick_query:
        user_input = st.session_state.quick_query
        st.session_state.quick_query = None
    else:
        user_input = None
    
    # Chat input
    if prompt := st.chat_input("Ask me about calendar scheduling...") or user_input:
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                success, response = run_async_in_streamlit(agent.process_message(prompt, for_streamlit=True))
                
                if success:
                    st.write(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    })
                else:
                    error_msg = f"❌ Error: {response}"
                    st.error(error_msg)
                    
                    # Add error to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now()
                    })
                
                st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    # Footer with additional controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("Refresh Agent", key="refresh_agent"):
            # Clear the cached agent and force recreation
            get_agent.clear()
            st.session_state.agent_initialized = False
            st.rerun()
    
    with col3:
        if st.button("Cleanup Agent", key="cleanup_agent"):
            if st.session_state.agent_initialized:
                with st.spinner("Cleaning up agent resources..."):
                    run_async_in_streamlit(agent.cleanup())
                    st.session_state.agent_initialized = False
                    st.success("✅ Agent resources cleaned up")
                    st.rerun()
    
    # Debug info (collapsible)
    with st.expander("Debug Information"):
        if st.session_state.agent_initialized:
            agent_status = run_async_in_streamlit(agent.get_agent_status())
            st.json(agent_status)
        else:
            st.info("Agent not initialized")

if __name__ == "__main__":
    main()
