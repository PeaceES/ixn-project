"""
Streamlit UI wrapper that uses subprocess to call the terminal agent.
This approach eliminates async conflicts and leverages the working terminal code.
"""

import streamlit as st
import subprocess
import json
import logging
import os
import sys
from datetime import datetime
from typing import Tuple

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
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)


def run_agent_query(user_input: str) -> Tuple[bool, str]:
    """
    Run a single query through the terminal agent using subprocess.
    
    Returns:
        Tuple[bool, str]: (success, response/error_message)
    """
    try:
        # Prepare the input for the subprocess
        process_input = f"{user_input}\n"
        
        # Get the current working directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use the original working main.py instead of main_single_query.py
        # This bypasses all the API compatibility issues we introduced
        main_input = f"{user_input}\nexit\n"
        
        # Run the single-query version of main.py using the working GUI Python interpreter
        # Try different Python interpreters that might work
        python_paths = [
            "/usr/local/bin/python",  # System Python (likely what GUI uses)
            "/usr/bin/python3",       # Alternative system Python
            sys.executable,           # Current Python (fallback)
        ]
        
        last_error = None
        for python_path in python_paths:
            try:
                result = subprocess.run(
                    [python_path, "main.py"],
                    input=main_input,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                    cwd=current_dir
                )
                # If no error and got output, use this interpreter
                if result.returncode == 0 or "Agent response:" in result.stdout:
                    break
            except Exception as e:
                last_error = e
                continue
        else:
            # If all failed, return the last error
            if last_error:
                return False, f"All Python interpreters failed. Last error: {last_error}"
        
        # Check if the process completed successfully
        if result.returncode != 0:
            return False, f"Process failed with return code {result.returncode}:\n{result.stderr}"
        
        # Parse the output from main.py
        output = result.stdout.strip()
        
        # Look for "Agent response:" in the output
        if "Agent response:" in output:
            # Extract the response after "Agent response:"
            lines = output.split('\n')
            response_lines = []
            found_response = False
            
            for line in lines:
                if "Agent response:" in line:
                    found_response = True
                    # Get the response part after "Agent response:"
                    response_part = line.split("Agent response:", 1)[-1].strip()
                    if response_part:
                        response_lines.append(response_part)
                elif found_response and line.strip() and not line.startswith("Raw response:") and not line.startswith("Response type:"):
                    response_lines.append(line.strip())
                elif found_response and ("Enter your query" in line or "Starting async program" in line):
                    break
            
            if response_lines:
                return True, '\n'.join(response_lines)
        
        # Fallback - look for any meaningful output
        if "Error:" in output:
            return False, "Agent encountered an error"
        elif output:
            return True, "Agent processed the request but output format was unexpected"
        else:
            return False, "No response from agent"
            
    except subprocess.TimeoutExpired:
        return False, "Query timed out after 2 minutes. Please try a simpler request."
    except Exception as e:
        return False, f"Subprocess error: {str(e)}"


def display_example_queries():
    """Display example queries in sidebar."""
    st.sidebar.markdown("## 💡 Example Queries")
    
    examples = [
        "Show me all available rooms",
        "Check if the Main Conference Room is available tomorrow at 2pm",
        "Schedule a meeting in the Alpha Meeting Room for tomorrow at 3pm",
        "I want to book the Drama Studio for a rehearsal next Friday",
        "What events are scheduled for this week?",
        "Find a large conference room for 20 people next Monday"
    ]
    
    for i, example in enumerate(examples):
        if st.sidebar.button(f"📝 {example[:35]}...", key=f"example_{i}"):
            st.session_state.quick_query = example


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">📅 Calendar Scheduling Agent</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'quick_query' not in st.session_state:
        st.session_state.quick_query = None
    
    # Sidebar
    display_example_queries()
    
    # Add welcome message if no messages yet
    if not st.session_state.messages:
        welcome_msg = """
**Welcome to the Calendar Scheduling Agent!** 🎉

I can help you with:
- 🏢 Listing available rooms
- 📅 Checking room availability  
- 📝 Scheduling meetings and events
- 👀 Viewing current events
- 🗓️ Managing your calendar

Try asking me something like "Show me all available rooms" or use the example queries in the sidebar!
        """
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.now()
        })
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("error"):
                st.error(message["content"])
            else:
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
        
        # Process with agent using subprocess
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing your request..."):
                success, response = run_agent_query(prompt)
                
                if success:
                    st.write(response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    })
                else:
                    error_msg = f"❌ **Error:** {response}"
                    st.error(error_msg)
                    # Add error to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "error": True,
                        "timestamp": datetime.now()
                    })
                
                st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    # Footer controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        st.write("🔄 Each query runs fresh")
    
    with col3:
        if st.button("ℹ️ About", key="about"):
            st.info("""
            This UI runs your terminal agent as a subprocess for each query.
            
            **Benefits:**
            - ✅ No async conflicts
            - ✅ Uses proven terminal code
            - ✅ Clean process isolation
            - ✅ Consistent behavior
            """)


if __name__ == "__main__":
    main()
