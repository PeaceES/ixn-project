# Calendar Scheduler Agent: Azure AI Agent Service Presentation

## Overview
A comprehensive 5-minute presentation on the Calendar Scheduler Agent built with Azure AI Agent Service, showcasing event booking, shared thread communication, and inter-agent coordination.

---

## 🎯 **Presentation Outline**

### **Slide 1: System Architecture Overview (1 minute)**

**What is the Calendar Scheduler Agent?**
- An intelligent calendar management system built on Azure AI Agent Service
- Handles room booking, event scheduling, and availability checking for a university campus
- Uses Model Context Protocol (MCP) for reliable calendar service communication
- Features real-time shared thread communication between agents

**Key Technologies:**
- Azure AI Agent Service (Core agent framework)
- Model Context Protocol (MCP) for calendar operations
- Azure AI Foundry for development and deployment
- FastAPI-based MCP server for calendar data management

---

### **Slide 2: Core Agent Architecture (1 minute)**

**Agent Core Components:**

```python
class CalendarAgentCore:
    """Core calendar agent functionality."""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self.thread: Optional[AgentThread] = None
        self.project_client: Optional[AIProjectClient] = None
        self.toolset = AsyncToolSet()
        self.utilities = Utilities()
        self.mcp_client = CalendarMCPClient()
        self.shared_thread_id: Optional[str] = None  # ← Shared communication thread
        self.functions = None
        self._initialize_functions()
```

**Agent Function Tools:**
```python
def _initialize_functions(self):
    """Initialize the function tools."""
    self.functions = AsyncFunctionTool([
        self.get_events_via_mcp,           # View calendar events
        self.check_room_availability_via_mcp,  # Check room availability
        self.get_rooms_via_mcp,            # List available rooms
        self.schedule_event_with_organizer, # Book events
    ])
```

---

### **Slide 3: Event Booking Process (1 minute)**

**How Event Booking Works:**

**Step 1: User Request Processing**
```python
async def process_message(self, message: str, for_streamlit: bool = False):
    """Process a message with the agent."""
    await self.project_client.agents.create_message(
        thread_id=self.thread.id,
        role="user",
        content=message,
    )
    
    # Create stream with function tools
    stream = await self.project_client.agents.create_stream(
        thread_id=self.thread.id,
        agent_id=self.agent.id,
        event_handler=stream_handler,
        instructions=self.agent.instructions,
    )
```

**Step 2: Room Availability Check**
```python
async def check_room_availability_via_mcp(self, room_id: str, start_time: str, end_time: str):
    """Check room availability via MCP server."""
    health = await self.mcp_client.health_check()
    if not health.get("status") == "healthy":
        return json.dumps({"success": False, "error": "MCP server not available"})
    
    result = await self.mcp_client.check_room_availability_via_mcp(room_id, start_time, end_time)
    return json.dumps(result)
```

**Step 3: Event Creation**
```python
async def schedule_event_with_organizer(self, room_id: str, title: str, 
                                       start_time: str, end_time: str, organizer: str):
    """Schedule an event with organizer information."""
    result = await self.schedule_event_via_mcp(
        title=title,
        start_time=start_time,
        end_time=end_time,
        room_id=room_id,
        organizer=organizer
    )
    return result
```

---

### **Slide 4: Shared Thread Communication (1 minute)**

**How Agents Communicate via Shared Threads:**

**Creating Shared Communication Thread:**
```python
async def initialize_agent(self):
    """Initialize the agent with shared thread setup."""
    # Create main conversation thread
    self.thread = await self.project_client.agents.create_thread()
    
    # Create shared communication thread for inter-agent communication
    shared_thread = await self.project_client.agents.create_thread()
    self.shared_thread_id = shared_thread.id
    
    # Post initialization event to shared thread
    event_payload = {
        "event": "initialized",
        "message": "Calendar agent is now active and ready to schedule events",
        "updated_by": "calendar-agent"
    }
    await self.project_client.agents.create_message(
        thread_id=shared_thread.id,
        role="user",
        content=json.dumps(event_payload)
    )
```

**Event Posting to Shared Thread:**
```python
# When an event is successfully scheduled
async def post_event_to_shared_thread(self, event_data):
    """Post event updates to shared thread for other agents."""
    notification = {
        "event": "event_scheduled",
        "event_id": event_data["id"],
        "title": event_data["title"],
        "room": event_data["room_id"],
        "start_time": event_data["start_time"],
        "end_time": event_data["end_time"],
        "organizer": event_data["organizer"],
        "updated_by": "calendar-agent",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await self.project_client.agents.create_message(
        thread_id=self.shared_thread_id,
        role="user",
        content=json.dumps(notification)
    )
```

---

### **Slide 5: MCP Server Integration & Communication Agent (1 minute)**

**MCP Server Calendar Operations:**

**MCP Server Event Creation:**
```python
@app.post("/calendars/{calendar_id}/events")
async def create_event(calendar_id: str, payload: CreateEventRequest):
    """Create a new calendar event with full validation."""
    # 1. Validate user permissions
    has_permission, permission_msg = validate_user_permissions(payload.user_id, calendar_id)
    
    # 2. Validate calendar exists
    calendar_exists, calendar_msg, calendar_info = validate_calendar_exists(calendar_id)
    
    # 3. Check for time conflicts
    has_conflicts, conflicts = check_time_conflicts(calendar_id, payload.start_time, payload.end_time)
    
    if has_conflicts:
        raise HTTPException(status_code=409, detail=f"Time conflict with existing events")
    
    # 4. Create and save event
    event = {
        "id": str(uuid.uuid4()),
        "calendar_id": calendar_id,
        "title": payload.title,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "organizer": payload.user_id,
        "status": "confirmed"
    }
    
    events_data["events"].append(event)
    await save_events()
    
    return {"success": True, "event": event}
```

**Communication Agent Reading Shared Thread:**
```python
class CommunicationAgent:
    """Agent that monitors shared thread for calendar events."""
    
    async def monitor_shared_thread(self):
        """Monitor shared thread for calendar updates."""
        while True:
            # Get latest messages from shared thread
            messages = await self.project_client.agents.list_messages(
                thread_id=self.shared_thread_id
            )
            
            for message in messages.data:
                try:
                    content = json.loads(message.content[0].text.value)
                    
                    if content.get("event") == "event_scheduled":
                        await self.handle_event_notification(content)
                    elif content.get("event") == "initialized":
                        await self.handle_agent_initialization(content)
                        
                except json.JSONDecodeError:
                    continue  # Skip non-JSON messages
            
            await asyncio.sleep(5)  # Poll every 5 seconds
    
    async def handle_event_notification(self, event_data):
        """Handle new event notifications from calendar agent."""
        # Send notifications, update dashboards, etc.
        notification_message = f"""
        🎉 New Event Scheduled!
        Title: {event_data['title']}
        Room: {event_data['room']}
        Time: {event_data['start_time']} - {event_data['end_time']}
        Organizer: {event_data['organizer']}
        """
        
        # Post to notification channels, update UI, etc.
        await self.send_notification(notification_message)
```

---

## 🚀 **Key Features Demonstrated**

### **1. Real-time Event Booking**
- User requests room booking through natural language
- Agent checks availability via MCP server
- Validates room conflicts and permissions
- Creates event and confirms booking

### **2. Shared Thread Communication**
- Multiple agents share a common communication thread
- Events are posted as JSON messages to shared thread
- Communication agent monitors and processes updates
- Enables real-time coordination between agents

### **3. MCP Protocol Integration**
- FastAPI-based MCP server handles calendar operations
- RESTful API endpoints for CRUD operations
- Health checking and error handling
- Persistent data storage in JSON files

### **4. Azure AI Agent Service Features**
- Function calling for calendar operations
- Code interpreter for data visualization
- Streaming responses for real-time interaction
- Multi-language support with custom fonts

---

## 📊 **Live Demo Flow**

**User:** "I need to book the Main Conference Room for a team meeting tomorrow at 2 PM"

**Agent Process:**
1. **Parse Request** → Extract room, time, event details
2. **Check Availability** → Query MCP server for room conflicts
3. **Validate Booking** → Ensure room is available during requested time
4. **Create Event** → Book the room via MCP server
5. **Confirm & Notify** → Post event to shared thread for other agents

**Shared Thread Message:**
```json
{
  "event": "event_scheduled",
  "event_id": "abc123",
  "title": "Team Meeting",
  "room": "main-conference-room",
  "start_time": "2025-07-17T14:00:00",
  "end_time": "2025-07-17T15:00:00",
  "organizer": "john.doe",
  "updated_by": "calendar-agent"
}
```

**Communication Agent Response:**
- Sends email notifications to participants
- Updates dashboard displays
- Logs event for reporting
- Triggers any automated workflows

---

## 🎯 **Key Takeaways**

1. **Azure AI Agent Service** provides robust framework for building intelligent agents
2. **MCP Protocol** enables reliable, structured communication with external services
3. **Shared Threads** facilitate seamless inter-agent communication and coordination
4. **Function Tools** allow agents to perform complex, multi-step operations
5. **Real-time Streaming** provides responsive user experiences
6. **Error Handling** ensures robust operation with fallback mechanisms

This architecture demonstrates how modern AI agents can work together to solve complex, real-world problems through structured communication and shared data management.

---

## 🔧 **Technical Implementation Notes**

- **Agent Initialization**: Creates both conversation and shared communication threads
- **Function Registration**: Tools are registered with Azure AI Agent Service
- **MCP Health Monitoring**: Continuous health checks ensure service availability
- **JSON Communication**: Structured data exchange between agents
- **Async Operations**: Non-blocking operations for better performance
- **Error Recovery**: Graceful handling of service unavailability

This presentation showcases a production-ready calendar scheduling system that demonstrates best practices for multi-agent coordination using Azure AI Agent Service.
