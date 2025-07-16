# Calendar Scheduling Agent

This repository contains a Calendar Scheduling Agent with two interfaces:

## 🖥️ Terminal Interface (`main.py`)
The original command-line interface for development and debugging.

### Usage:
```bash
python main.py
```

### Features:
- Interactive command-line interface
- Colored terminal output
- Direct debug information
- Ideal for development and testing

## 🌐 Streamlit Web Interface (`streamlit_app.py`)
A modern web interface for user-friendly interaction.

### Usage:
```bash
streamlit run streamlit_app.py
```

### Features:
- Modern chat interface
- Real-time status monitoring
- Quick action buttons
- Example queries
- Visual feedback and error handling
- Responsive design

## 🏗️ Architecture

Both interfaces use the shared `agent_core.py` module which contains:
- Core agent functionality
- MCP client integration
- Azure AI Projects integration
- Reusable business logic

### Files:
- `agent_core.py` - Core agent functionality (shared)
- `main.py` - Terminal interface
- `streamlit_app.py` - Web interface
- `requirements.txt` - Dependencies

## 🚀 Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env`:
```
MODEL_DEPLOYMENT_NAME=your-model-deployment
PROJECT_CONNECTION_STRING=your-project-connection-string
USER_DIRECTORY_URL=your-user-directory-url
```

3. Choose your interface:
   - For development: `python main.py`
   - For user testing: `streamlit run streamlit_app.py`

## 💬 Example Queries

Try these example queries with either interface:

- "Show me all available rooms"
- "Check if the Main Conference Room is available tomorrow at 2pm"
- "Schedule a meeting in the Alpha Meeting Room for tomorrow at 3pm"
- "I want to book the Drama Studio for a rehearsal next Friday"
- "What events are scheduled for this week?"

## 🔧 Development Workflow

1. **Develop & Debug**: Use `main.py` for quick testing and debugging
2. **Test Features**: Use `streamlit_app.py` for user experience testing
3. **Share**: Deploy Streamlit app for stakeholder demos

## 🛠️ Technical Details

### Agent Capabilities:
- Room availability checking
- Event scheduling
- Event listing
- MCP server integration
- User directory access
- Multi-language support (via code interpreter)

### Status Monitoring:
- MCP server health
- User directory connectivity
- Agent initialization status
- Real-time error handling

## 📝 Notes

- Both interfaces share the same underlying agent logic
- Terminal interface is better for debugging
- Streamlit interface is better for user interaction
- Agent resources are automatically managed
- MCP server connectivity is monitored in real-time
