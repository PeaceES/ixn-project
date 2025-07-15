# Calendar Scheduler Agent

An intelligent calendar scheduling assistant built with Azure AI Agent Service, designed specifically for university campus environments with group-based booking permissions.

## Overview

This agent serves as a smart calendar management system that helps university students, faculty, and staff efficiently schedule meetings, events, and room bookings while respecting organizational permissions and group-based access controls.

## Key Features

### 🗓️ **Calendar Management**
- View and manage calendar events across the university system
- Display upcoming events with detailed information
- Track scheduled meetings and activities

### 🏢 **Room Booking System**
- Check real-time room availability for specific dates and times
- Browse available rooms with capacity and location details
- Smart scheduling that prevents double-bookings

### 👥 **Group-Based Permissions**
- **Group-centric booking**: Users must book rooms through authorized groups (societies, departments, clubs)
- **Permission verification**: Automatic checking of user group memberships and room access rights
- **Authorized access control**: Ensures only authorized groups can book specific rooms

### 🔧 **Advanced Capabilities**
- **Code Interpreter**: Generate data visualizations and charts for event analytics
- **Multilingual Support**: Handle scheduling requests in multiple languages with custom font support
- **MCP Integration**: Uses Model Context Protocol for reliable calendar service communication
- **Real-time Health Monitoring**: Checks service availability before operations

## How It Works

### Group-Based Booking Flow
1. **User Identification**: User provides their user ID (e.g., "john.doe")
2. **Group Selection**: Agent shows available groups the user belongs to
3. **Permission Check**: Verifies if the selected group can book the requested room
4. **Room Booking**: Schedules the event if all permissions are valid
5. **Confirmation**: Provides booking confirmation with event details

### Available Functions
- `get_events_via_mcp()` - Retrieve calendar events
- `check_room_availability_via_mcp()` - Check if rooms are available
- `get_rooms_via_mcp()` - List all available rooms
- `schedule_group_event()` - Book rooms with permission checking
- `get_user_groups()` - Show user's group memberships
- `get_group_rooms()` - Display rooms accessible to a group

## Example Usage

```
User: "I want to book lecture hall A for a meeting"

Agent: "What's your user ID?"
User: "john.doe"

Agent: "What group are you booking for? You belong to:
- Engineering Society
- Computer Science Department"

User: "Engineering Society"

Agent: "✅ Permission verified! Engineering Society can book Lecture Hall A.
When would you like to schedule your meeting?"
```

## Demo Users

The system includes sample users for testing:
- **john.doe** - Engineering Society, Computer Science Dept
- **alice.chen** - Engineering Society, Robotics Club, Computer Science Dept
- **sarah.jones** - Drama Club
- **alex.brown** - Student Government
- **prof.johnson** - Computer Science Dept

## Technical Architecture

### Built With
- **Azure AI Agent Service** - Core agent framework
- **Model Context Protocol (MCP)** - Calendar service communication
- **Python 3.8+** - Implementation language
- **Azure AI Foundry** - Development and deployment platform

### Key Components
- **Agent Core** (`main.py`) - Main agent logic and conversation handling
- **MCP Client** - Interface for calendar service operations
- **Permission System** - Group-based access control
- **Stream Handler** - Real-time response processing
- **Utilities** - File handling and instruction management

## Getting Started

1. **Prerequisites**: Ensure you have Azure AI Foundry access and required credentials
2. **Configuration**: Set up your `PROJECT_CONNECTION_STRING` and other environment variables
3. **Installation**: Install dependencies from `requirements.txt`
4. **Run**: Execute `python main.py` to start the agent

## Security & Permissions

The agent implements robust security measures:
- **Group membership verification** before any booking
- **Room access control** based on organizational policies
- **User authentication** through university systems
- **Audit trail** of all booking activities

## Future Enhancements

- Integration with university authentication systems
- Mobile app compatibility
- Advanced scheduling algorithms
- Resource conflict resolution
- Analytics and reporting dashboard

---

*Built for university environments where organized, permission-based room booking is essential for smooth campus operations.*