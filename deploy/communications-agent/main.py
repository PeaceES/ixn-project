import asyncio
import os
import httpx
import logging
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from shared.services.db_shared import get_shared_thread

from utilities import Utilities

load_dotenv()

logger = logging.getLogger("comms_agent")

def load_shared_thread_id():
    row = get_shared_thread()
    tid = (row or {}).get("thread_id")
    if not tid:
        tid = os.getenv("SHARED_THREAD_ID")  # optional fallback
    logger.info(f"[Comms] Using shared thread id = {tid}")
    return tid

SHARED_THREAD_ID = load_shared_thread_id()

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")

utilities = Utilities()

def fetch_user_directory():
    """Fetch user directory from uploaded Azure resource to verify agent access."""
    url = os.getenv("USER_DIRECTORY_URL")
    if not url:
        print("USER_DIRECTORY_URL not found in environment variables")
        return {}
    
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        print("Successfully accessed user directory")
        return response.json()
    except Exception as e:
        print(f"Failed to load user directory: {e}")
        return {}

async def create_test_agent():
    async with AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    ) as project_client:
        # Load instructions from external file
        instructions = utilities.load_instructions("general_instructions.txt")
        
        agent = await project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT_NAME,
            name="Comms Agent",
            instructions=instructions,
            temperature=0.2,
        )
        utilities.log_msg_green(f"Agent created with ID: {agent.id}")

        thread = await project_client.agents.create_thread()
        utilities.log_msg_green(f"Thread created with ID: {thread.id}")

        return agent, thread

async def read_last_message_from_thread(project_client: AIProjectClient, thread_id: str):
    """Read the last posted message from a thread."""
    try:
        # Get messages from the thread (they are returned in reverse chronological order by default)
        messages = await project_client.agents.list_messages(thread_id=thread_id, limit=1)
        
        if messages.data:
            last_message = messages.data[0]  # First item is the most recent
            utilities.log_msg_purple(f"Last message ID: {last_message.id}")
            utilities.log_msg_purple(f"Message role: {last_message.role}")
            utilities.log_msg_purple(f"Message created at: {last_message.created_at}")
            
            # Extract and display the message content
            if last_message.content:
                for content_item in last_message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        utilities.log_msg_green(f"Message content: {content_item.text.value}")
                    elif hasattr(content_item, 'type'):
                        utilities.log_msg_purple(f"Content type: {content_item.type}")
            
            return last_message
        else:
            utilities.log_msg_purple("No messages found in the thread.")
            return None
            
    except Exception as e:
        utilities.log_msg_purple(f"Error reading messages: {str(e)}")
        return None

async def read_messages_from_existing_thread(thread_id: str):
    """Connect to an existing thread and read messages from it."""
    async with AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    ) as project_client:
        utilities.log_msg_green(f"Connecting to existing thread: {thread_id}")
        
        # Read the last message
        last_message = await read_last_message_from_thread(project_client, thread_id)
        
        if last_message:
            utilities.log_msg_green("Successfully read the last message from the thread.")
        else:
            utilities.log_msg_purple("No messages found or error occurred.")

async def monitor_shared_thread(thread_id: str, check_interval: int = 30):
    """Monitor a shared thread for new messages from the scheduler agent."""
    utilities.log_msg_green(f"Starting to monitor thread: {thread_id}")
    utilities.log_msg_green(f"Check interval: {check_interval} seconds")
    
    last_known_message_id = None

    # Import the logger
    from message_logger import log_message

    async with AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    ) as project_client:

        while True:
            try:
                # Check for new messages
                new_messages = await utilities.check_for_new_messages(
                    project_client, thread_id, last_known_message_id
                )

                if new_messages:
                    utilities.log_msg_green(f"Found {len(new_messages)} new message(s)!")

                    for message in reversed(new_messages):  # Process in chronological order
                        utilities.log_msg_purple(f"Processing new message: {message.id}")
                        utilities.log_msg_purple(f"Message role: {message.role}")
                        utilities.log_msg_purple(f"Message created at: {message.created_at}")

                        # Display message content for all messages
                        message_content = ""
                        if message.content:
                            for content_item in message.content:
                                if hasattr(content_item, 'text') and content_item.text:
                                    message_content = content_item.text.value
                                    utilities.log_msg_green(f"📧 MESSAGE CONTENT: {message_content}")

                                    # Save message to log file
                                    log_message(f"[{message.created_at}] {message.role}: {message_content}")

                                    # Try to parse and interpret the message content
                                    await interpret_message_content(message_content)

                                elif hasattr(content_item, 'type'):
                                    utilities.log_msg_purple(f"Content type: {content_item.type}")

                        # Check if it's from the scheduler agent (not from this comms agent)
                        if message.role == "assistant" and message_content:
                            utilities.log_msg_green("🤖 New message from scheduler agent detected!")

                            # Process scheduler-specific messages
                            await process_scheduler_message(message_content, project_client, thread_id)
                        elif message.role == "user" and message_content:
                            utilities.log_msg_green("👤 New user message detected!")

                        # Update the last known message ID
                        last_known_message_id = message.id

                else:
                    utilities.log_msg_purple("No new messages found.")

                # Wait before checking again
                await asyncio.sleep(check_interval)

            except KeyboardInterrupt:
                utilities.log_msg_green("Monitoring stopped by user.")
                break
            except Exception as e:
                utilities.log_msg_purple(f"Error during monitoring: {str(e)}")
                await asyncio.sleep(check_interval)

def extract_event_details(parsed_content):
    """Extract organiser, attendee, and email information from event data."""
    import re
    from util_email import load_org_structure
    
    organiser_field = parsed_content.get("organizer", "")
    organiser_email = None
    organiser_name = None
    # If organiser_field looks like an email, use it directly
    email_regex = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    if re.fullmatch(email_regex, organiser_field.strip()):
        organiser_email = organiser_field.strip()
        organiser_name = organiser_field.strip()
    else:
        # Try to extract name from e.g. "Allison Hill (course: Civil Engineering)"
        organiser_match = re.match(r"([^(]+)", organiser_field)
        organiser_name = organiser_match.group(1).strip() if organiser_match else organiser_field.strip()
        # Try to look up organiser email by name
        org_structure = load_org_structure("shared/org_structure.json")
        for user in org_structure.get("users", []):
            if user["name"].lower() == organiser_name.lower():
                organiser_email = user["email"]
                break
    # Try to extract course or society
    society_match = re.search(r"society: ([^)]+)", organiser_field)
    course_match = re.search(r"course: ([^)]+)", organiser_field)
    course_or_society = society_match.group(1).strip() if society_match else (course_match.group(1).strip() if course_match else "")
    # Attendees: collect all possible emails
    recipients = set()
    if organiser_email:
        recipients.add(organiser_email)
    # attendee_email (single)
    attendee_email = parsed_content.get("attendee_email")
    if attendee_email:
        recipients.add(attendee_email)
    # attendees (list)
    attendees_list = parsed_content.get("attendees")
    if isinstance(attendees_list, list):
        for att in attendees_list:
            if att:
                recipients.add(att)
    # If attendee_email is null and course/society is present, use its email
    if not attendee_email and course_or_society:
        org_structure = load_org_structure("shared/org_structure.json")
        # Try course
        for course in org_structure.get("courses", []):
            if course["name"].lower() == course_or_society.lower():
                recipients.add(course["email"])
        # Try society
        for soc in org_structure.get("societies", []):
            if soc["name"].lower() == course_or_society.lower():
                recipients.add(soc["email"])
    # Format attendee list for email body
    attendee_list = ", ".join(sorted({attendee_email or ""} | set(attendees_list or []))) if (attendee_email or attendees_list) else "(not specified)"
    return {
        'organiser_name': organiser_name,
        'course_or_society': course_or_society,
        'organiser_email': organiser_email,
        'attendee_email': attendee_email,
        'attendee_list': attendee_list,
        'recipients': list(sorted(recipients))
    }

def send_event_notification_email(event_type, parsed_content, event_details):
    """Send email notification for any event type."""
    import re
    from send_email import send_email
    
    # Load template
    with open("shared/general_instructions.txt", "r") as f:
        template = f.read()
    
    # Determine which template to use based on event type
    template_mapping = {
        "event_created": ("EMAIL_SUBJECT_CREATED", "EMAIL_BODY_CREATED"),
        "event_updated": ("EMAIL_SUBJECT_UPDATED", "EMAIL_BODY_UPDATED"),
        "event_cancelled": ("EMAIL_SUBJECT_CANCELLED", "EMAIL_BODY_CANCELLED"),
        "event_canceled": ("EMAIL_SUBJECT_CANCELLED", "EMAIL_BODY_CANCELLED"),  # Alternative spelling
        "event_rescheduled": ("EMAIL_SUBJECT_RESCHEDULED", "EMAIL_BODY_RESCHEDULED")
    }
    
    subject_key, body_key = template_mapping.get(event_type, ("EMAIL_SUBJECT_CREATED", "EMAIL_BODY_CREATED"))
    
    # Extract subject and body templates
    subject_match = re.search(rf'{subject_key} = "([^"]+)"', template)
    body_match = re.search(rf'{body_key} = """([\s\S]+?)"""', template)
    
    subject_template = subject_match.group(1) if subject_match else f"Event Notification: {{event_name}}"
    body_template = body_match.group(1) if body_match else "Event notification."
    
    # Prepare template variables
    template_vars = {
        'event_name': parsed_content.get("title", "Event"),
        'organiser_name': event_details['organiser_name'],
        'course_or_society': event_details['course_or_society'],
        'attendee_list': event_details['attendee_list'],
        'event_datetime': f"{parsed_content.get('start_time', '')} to {parsed_content.get('end_time', '')}",
        'event_location': parsed_content.get("room_id", ""),
        'organiser_email': event_details['organiser_email'] if event_details['organiser_email'] else "(not found)"
    }
    
    # Add event-specific variables
    if event_type in ["event_updated"]:
        template_vars['changes_description'] = parsed_content.get("message", "Details updated")
    elif event_type in ["event_cancelled", "event_canceled"]:
        template_vars['cancellation_reason'] = parsed_content.get("message", "No reason provided")
    elif event_type == "event_rescheduled":
        template_vars['previous_datetime'] = parsed_content.get("previous_time", "Previous time not specified")
    
    # Fill in templates
    subject = subject_template.format(**template_vars)
    body = body_template.format(**template_vars)
    
    # Send email
    if event_details['recipients']:
        send_email(event_details['recipients'], subject, body)
        utilities.log_msg_green(f"📧 Email sent to: {', '.join(event_details['recipients'])}")
        return True
    else:
        utilities.log_msg_purple("No valid email recipients found.")
        return False

async def interpret_message_content(message_content: str):
    """Interpret and provide a human-readable description of the message content."""
    try:
        import json
        
        # Try to parse as JSON first
        parsed_content = json.loads(message_content)
        if isinstance(parsed_content, dict):
            event_type = parsed_content.get("event", "unknown")
            message_text = parsed_content.get("message", "")
            updated_by = parsed_content.get("updated_by", "unknown")
            
            # Process events that require email notifications
            if event_type in ["event_created", "event_updated", "event_cancelled", "event_canceled", "event_rescheduled"]:
                # Extract event details for email
                event_details = extract_event_details(parsed_content)
                
                # Log event type specific messages
                if event_type == "event_created":
                    utilities.log_msg_green("📅 EVENT CREATED: A new event has been scheduled!")
                elif event_type == "event_updated":
                    utilities.log_msg_green("📝 EVENT UPDATED: An existing event has been modified!")
                elif event_type in ["event_cancelled", "event_canceled"]:
                    utilities.log_msg_green("❌ EVENT CANCELLED: An event has been cancelled!")
                elif event_type == "event_rescheduled":
                    utilities.log_msg_green("🔄 EVENT RESCHEDULED: An event has been rescheduled!")
                
                # Send email notification
                send_event_notification_email(event_type, parsed_content, event_details)
            
            # Handle other event types without email notifications
            elif event_type == "initialized":
                utilities.log_msg_green("🟢 SYSTEM: Calendar agent has been initialized and is ready")
            elif event_type == "reminder":
                utilities.log_msg_green("⏰ REMINDER: Upcoming event notification!")
                if message_text:
                    utilities.log_msg_green(f"   Details: {message_text}")
            else:
                utilities.log_msg_green(f"📋 EVENT: {event_type.upper()}")
                if message_text:
                    utilities.log_msg_green(f"   Details: {message_text}")
            
            utilities.log_msg_purple(f"   Updated by: {updated_by}")
        else:
            utilities.log_msg_green(f"📋 PARSED CONTENT: {parsed_content}")
    except Exception as e:
        utilities.log_msg_purple(f"Error in interpret_message_content: {e}")

async def process_scheduler_message(message_content: str, project_client: AIProjectClient, thread_id: str):
    """Process a message from the scheduler agent and potentially send a response."""
    utilities.log_msg_green(f"🤖 Processing scheduler agent message...")
    
    # Example: Check if the message contains scheduling information
    content_lower = message_content.lower()
    
    if any(keyword in content_lower for keyword in ["schedule", "meeting", "appointment", "event"]):
        utilities.log_msg_green("📋 SCHEDULING-RELATED MESSAGE DETECTED!")
        
        # You can add your notification logic here
        # For example:
        # - Send email notifications
        # - Update a database  
        # - Send SMS messages
        # - Post to Slack/Teams
        
        # Optionally, respond back to the thread
        response_message = f"Communications agent acknowledged scheduling update"
        
        await project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=f"[COMMS AGENT] {response_message}"
        )
        
        utilities.log_msg_green("✅ Sent acknowledgment back to the thread.")
    
    elif any(keyword in content_lower for keyword in ["canceled", "cancelled"]):
        utilities.log_msg_green("❌ CANCELLATION MESSAGE DETECTED!")
        # Add cancellation-specific logic here
        
    elif any(keyword in content_lower for keyword in ["changed", "updated", "modified"]):
        utilities.log_msg_green("📝 UPDATE MESSAGE DETECTED!")
        # Add update-specific logic here

def test_user_directory_access():
    """Test function to verify access to the user directory."""
    print("=== Testing User Directory Access ===")
    
    # Test user directory access
    print("Testing user directory access...")
    users = fetch_user_directory()
    if users:
        print(f"📋 User directory loaded successfully with {len(users)} entries")
        # Print first few users for verification (optional)
        for i, (key, value) in enumerate(list(users.items())[:3]):
            print(f"  Sample user {i+1}: {key} -> {value}")
    else:
        print("⚠️ User directory is empty or inaccessible")
    
    print("=== User Directory Test Complete ===")
    return users

async def main():
    """Main function to demonstrate reading from shared thread."""
    
    if not SHARED_THREAD_ID:
        utilities.log_msg_purple("ERROR: SHARED_THREAD_ID not found in environment variables!")
        utilities.log_msg_purple("Please set SHARED_THREAD_ID in your .env file")
        return
    
    utilities.log_msg_green(f"=== Communications Agent Starting ===")
    utilities.log_msg_green(f"Using shared thread ID: {SHARED_THREAD_ID}")
    
    # Test user directory access first
    test_user_directory_access()
    
    # Read the last message from the shared thread
    utilities.log_msg_green("=== Reading last message from shared thread ===")
    await read_messages_from_existing_thread(SHARED_THREAD_ID)
    
    # Optional: Start monitoring the shared thread for new messages
    utilities.log_msg_green("=== Starting thread monitoring ===")
    utilities.log_msg_purple("Press Ctrl+C to stop monitoring...")
    
    try:
        await monitor_shared_thread(SHARED_THREAD_ID, check_interval=10)
    except KeyboardInterrupt:
        utilities.log_msg_green("Monitoring stopped by user.")

if __name__ == "__main__":
    asyncio.run(main())
