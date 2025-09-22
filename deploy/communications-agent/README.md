# Communications Agent

This is a communications agent that can read and process messages from a shared thread with a scheduler agent in the same Azure AI Project.


- ✅ Read the last posted message from a shared thread
- ✅ Monitor a shared thread for new messages
- ✅ Process messages from the scheduler agent
- ✅ Send acknowledgments back to the thread
- ✅ Handle different message types and content

## Setup

1. Make sure you have the required environment variables set:
   ```bash
   PROJECT_CONNECTION_STRING=your_azure_project_connection_string
   MODEL_DEPLOYMENT_NAME=your_model_deployment_name
   ```

2. Optional: Set the shared thread ID as an environment variable:
   ```bash
   SHARED_THREAD_ID=thread_abc123xyz
   ```

## Usage

### Quick Check - Read Last Message

Use the simple check script to quickly read the last message from a shared thread:

```bash
python check_messages.py
```

Make sure to set the `THREAD_ID` variable in the script or the `SHARED_THREAD_ID` environment variable.

### Full Agent Functionality

Run the main agent with full functionality:

```bash
python main.py
```

### Key Functions

#### `read_last_message_from_thread(project_client, thread_id)`
- Reads the most recent message from a thread
- Returns message details including content, role, and timestamp
- Handles different content types (text, files, etc.)

#### `monitor_shared_thread(thread_id, check_interval)`
- Continuously monitors a thread for new messages
- Processes messages from the scheduler agent
- Can send acknowledgments back to the thread
- Configurable check interval (default: 30 seconds)

#### `process_scheduler_message(message_content, project_client, thread_id)`
- Processes messages from the scheduler agent
- Detects scheduling-related keywords
- Can trigger notifications or other actions
- Sends acknowledgments back to the thread

## Message Flow

1. **Scheduler Agent** posts a message to the shared thread
2. **Communications Agent** detects the new message
3. **Communications Agent** processes the message content
4. **Communications Agent** can:
   - Send notifications (email, SMS, Slack, etc.)
   - Update databases
   - Send acknowledgment back to the thread
   - Trigger other workflows

## Example Usage

```python
# Read the last message from a shared thread
last_message = await read_last_message_from_thread(project_client, "thread_abc123")

# Monitor a shared thread continuously
await monitor_shared_thread("thread_abc123", check_interval=10)

# Display recent messages from a thread
await utilities.display_thread_messages(project_client, "thread_abc123", limit=5)
```

## Monitoring Setup

To continuously monitor a shared thread:

1. Set the `existing_thread_id` variable in `main.py`
2. Uncomment the `monitor_shared_thread()` call
3. Run the script - it will continuously check for new messages

## Error Handling

The agent includes comprehensive error handling for:
- Connection issues
- Invalid thread IDs
- Message parsing errors
- Network timeouts

## Customization

You can customize the agent by:
- Modifying the message processing logic in `process_scheduler_message()`
- Adding custom notification methods
- Changing the monitoring interval
- Adding filters for specific message types
- Implementing custom response templates

## Integration Ideas

- **Email Notifications**: Send emails when schedule changes are detected
- **SMS Alerts**: Send text messages for urgent schedule updates
- **Slack/Teams Integration**: Post messages to communication channels
- **Database Updates**: Update scheduling databases with changes
- **Calendar Integration**: Sync with calendar applications
- **Webhook Triggers**: Trigger external systems via webhooks
