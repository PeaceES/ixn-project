# Quick Start: User Context Injection

## What's This?

When using the calendar agent through the web interface, the system automatically knows who you are from your login. You don't need to tell it your user ID when booking rooms!

## Terminal vs Web Behavior

### 🖥️ Terminal (No Change)
```bash
python main.py
```
```
You: I want to book a room
Agent: What's your user ID?
You: 5
Agent: Let me check what you can book for...
```

### 🌐 Web Interface (Enhanced!)
```
You: I want to book a room
Agent: I see you're John Doe (ID: 5). Let me check what you can book for...
```

## How to Use

### 1. Start the Web Server
```bash
python web_server.py
```

### 2. Login
- Go to http://localhost:8502
- Login with any email from the user list
- Your identity is now known to the system

### 3. Chat Naturally
- Just ask to book rooms without providing your ID
- The agent automatically knows who you are

## When Does It Work?

Context is injected for messages containing:
- "book", "schedule", "reserve"
- "meeting", "event", "room"
- "calendar", "available"
- "what can i book"

## Turn It Off (If Needed)

```bash
# Disable automatic context injection
export AUTO_INJECT_USER_CONTEXT=false
python web_server.py
```

Now the web interface will ask for your ID just like the terminal.

## Test It

```bash
# See how it works
python test_user_context.py
```

## That's It! 🎉

The agent is now smarter about knowing who you are when you use the web interface!
