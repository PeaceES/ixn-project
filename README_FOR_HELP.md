# Calendar Scheduling Agent - Current State Documentation

## Overview
This Calendar Scheduling Agent is built with Azure AI Agent Service and can manage room bookings and events through both a terminal interface and a Streamlit web UI.

## Current Architecture

### Working Components
- **`main.py`** - Terminal interface (WORKING)
- **`agent_core.py`** - Shared agent logic (WORKING)
- **MCP Server** - Calendar service backend (WORKING)

### Problem Component
- **`streamlit_app.py`** - Web UI (EVENT LOOP ISSUE)

## File Structure
```
src/python/workshop/
├── main.py                 # Terminal interface (WORKING)
├── agent_core.py           # Core agent logic (WORKING)
├── streamlit_app.py        # Web UI (event loop issue)
├── services/               # Backend services
│   ├── calendar_mcp_server.py     # MCP server backend
│   ├── mcp_client.py             # MCP client
│   └── microsoft_docs_mcp_client.py
├── agent/                  # Agent components
│   └── stream_event_handler.py
├── utils/                  # Utility functions
│   └── utilities.py
├── evaluation/             # Agent evaluation logic
├── models/                 # Data models
├── config/                 # Configuration files
├── tests/                  # All test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── manual/            # Manual test scripts
│   ├── debug/             # Debug utilities
│   └── *.py               # Test files
├── docs/                   # Documentation
│   ├── README_FOR_HELP.md
│   ├── README_INTERFACES.md
│   └── TESTING_SETUP.md
└── scripts/                # Utility scripts
```

## How to Run

### Prerequisites
**IMPORTANT: Start the MCP Calendar Server first!**

**Start MCP Calendar Server** (in a separate terminal):
   ```bash
   cd src/python/workshop
   python services/calendar_mcp_server.py
   ```
   Keep this running - both interfaces depend on it.

### Terminal Interface (Works)
```bash
cd src/python/workshop
python main.py
```

### Web Interface (Has Issues)
```bash
cd src/python/workshop
streamlit run streamlit_app.py
```

**Note:** Do not run both interfaces simultaneously as they will conflict with each other.

## The Problem: "Event loop is closed" Error

### What Works:
- Agent initialization succeeds
- File upload succeeds
- Streamlit UI loads properly

### What Fails:
- When processing messages through the agent
- Error: `Event loop is closed`
- Additional error: `Task was destroyed but it is pending!`

### Known Issues in Streamlit UI:
- **MCP Server Health Check**: The Streamlit UI incorrectly shows "MCP server unhealthy" even when the MCP server is running and functional (as proven by the working terminal interface)
- **False Status Indication**: This misleading status could cause confusion - the MCP server itself is working fine
- **Root Cause**: Both the health check issue and the event loop error likely stem from the same Streamlit + Azure SDK async integration problems

### Error Location:
- Occurs in `run_async_in_streamlit()` function
- Happens when calling `agent.process_message()` 
- Related to Azure SDK HTTP client cleanup timing

### Root Cause:
The issue appears to be a conflict between:
1. **Streamlit's event loop management**
2. **Azure AI SDK's async HTTP connections** 
3. **The `asyncio.run()` wrapper in a thread**

The Azure SDK creates HTTP connections that aren't being properly cleaned up when the event loop closes, causing the "Event loop is closed" error.

## Key Code Components

### Agent Core (`agent_core.py`)
- `CalendarAgentCore` class with all agent functionality
- Uses Azure AI Project Client with proper endpoint construction
- Handles MCP server communication
- **Status: Working in terminal, causes event loop issues in Streamlit**

### Async Wrapper (`streamlit_app.py`)
```python
def run_async_in_streamlit(coroutine):
    """This is where the event loop issue occurs"""
    def run_with_asyncio():
        return asyncio.run(coroutine)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_with_asyncio)
        return future.result(timeout=120)
```

## Environment Requirements
- Python 3.13
- Azure AI Projects SDK v1.0.0b12
- Azure AI Agents SDK v1.0.2
- Streamlit
- Other deps in requirements.txt

## Authentication
- Uses `DefaultAzureCredential()`
- Requires `PROJECT_CONNECTION_STRING` in `.env`

## TO FIX
1. **Investigate event loop cleanup** - The issue is likely in how the asyncio event loop lifecycle is being managed
2. **Fix MCP server health check** - The health check logic in Streamlit needs to be corrected (server is actually healthy)
3. **Consider alternative approaches**:
   - Different async wrapper patterns
   - Using Streamlit's native async support
   - Process-based separation instead of thread-based
4. **Azure SDK compatibility** - May need to investigate if there are Streamlit-specific patterns for Azure SDK usage

## Additional Notes
- Terminal version proves the agent logic is sound
- The issue is specifically the Streamlit + Azure SDK async integration
- MCP server must be running separately for both interfaces to work
- Ignore "MCP server unhealthy" status in Streamlit UI - it's a false indicator
