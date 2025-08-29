# User Context Handling in Web Interface

## Overview

When using the calendar agent through the web interface, the system can automatically inject user context so that users don't need to manually provide their ID when booking rooms. This improves the user experience by using the authentication information from the web login.

## How It Works

### 1. User Authentication
- Users log in through the web interface using their email
- The system maintains a session with the user's information (ID, name, email)

### 2. Context Injection Methods

#### Method 1: Per-Message Context (Primary Method)
When a user sends a message containing booking-related keywords, the system automatically prepends their user context:

```
[System: User context - ID: 5, Name: John Doe, Email: john@example.com]
I want to book a room for tomorrow
```

The agent is instructed to:
- Extract the user information from the system message
- Use the provided ID directly without asking for it
- Proceed with the booking flow

#### Method 2: Environment Variables (Alternative)
When the agent is started through the web interface, user context can be passed via environment variables:
- `AGENT_USER_ID`: The user's ID
- `AGENT_USER_NAME`: The user's name  
- `AGENT_USER_EMAIL`: The user's email

## Configuration

### Enable/Disable Auto-Injection
Set the environment variable `AUTO_INJECT_USER_CONTEXT` to control this feature:
- `true` (default): Automatically inject user context for booking-related messages
- `false`: Disable automatic context injection (agent will ask for user ID)

### Booking Keywords
The system detects booking intent when messages contain keywords like:
- book, schedule, reserve
- meeting, event, room
- calendar, available
- "what can i book"

## Example User Experience

### With Context Injection (Web Interface)
```
User: "I want to book the main lecture hall for tomorrow 2pm"
Agent: "I see you're John Doe (ID: 5). Let me check what you can book for..."
[Agent checks permissions and shows available entities]
```

### Without Context Injection (Terminal)
```
User: "I want to book the main lecture hall for tomorrow 2pm"
Agent: "What's your user ID?"
User: "5"
Agent: "Let me check what you can book for..."
```

## Implementation Details

### Web Server Changes
1. The `handle_send_message` function checks if:
   - User is authenticated
   - Message contains booking keywords
   - `AUTO_INJECT_USER_CONTEXT` is enabled

2. If all conditions are met, it prepends the user context to the message

### Agent Instructions
The agent instructions have been updated to:
1. Check for `[System: User context...]` messages
2. Extract user information when present
3. Skip asking for user ID if context is provided

## Security Considerations

- User context is only injected for authenticated users
- The context is only added to booking-related messages
- The system message format prevents users from spoofing context
- Context injection can be disabled via environment variable

## Testing

### Test with Context Injection
1. Set `AUTO_INJECT_USER_CONTEXT=true`
2. Log in through the web interface
3. Send a booking message
4. Verify the agent uses your ID without asking

### Test without Context Injection
1. Set `AUTO_INJECT_USER_CONTEXT=false`
2. Send a booking message
3. Verify the agent asks for your ID

## Troubleshooting

If the agent still asks for user ID:
1. Check if you're logged in
2. Verify `AUTO_INJECT_USER_CONTEXT` is set to `true`
3. Ensure your message contains booking-related keywords
4. Check the agent logs for context extraction
