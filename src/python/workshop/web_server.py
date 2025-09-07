"""
Flask Web Server for Calendar Scheduling Agent
Stage 4: Interactive Chat Interface
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit, disconnect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import subprocess
import signal
import psutil
import time
import threading
import queue
import json
import logging
from pathlib import Path

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Additional dev container friendly settings
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Feature flags
AUTO_INJECT_USER_CONTEXT = os.getenv('AUTO_INJECT_USER_CONTEXT', 'true').lower() == 'true'

# Paths
WORKSHOP_DIR = Path(__file__).parent
STATIC_DIR = WORKSHOP_DIR / 'static'
TEMPLATES_DIR = WORKSHOP_DIR / 'templates'

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
(STATIC_DIR / 'css').mkdir(exist_ok=True)
(STATIC_DIR / 'js').mkdir(exist_ok=True)

# Global variables for agent process management
agent_process = None
agent_start_time = None
agent_log_file = WORKSHOP_DIR / 'logs' / 'agent.log'
agent_output_queue = queue.Queue()
output_thread = None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, name, email, role, calendar_permissions=None):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.calendar_permissions = calendar_permissions or {}

def load_user_directory():
    """Load user directory from org_structure.json."""
    org_path = Path(__file__).parent.parent.parent / 'shared' / 'database' / 'data-generator' / 'org_structure.json'
    try:
        with open(org_path, 'r') as f:
            org_data = json.load(f)
        
        # Convert org_structure users to user directory format
        user_directory = {}
        for user in org_data.get('users', []):
            user_id = str(user.get('id', ''))
            user_directory[user_id] = {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'role': user.get('role_scope', ''),
                'department_id': user.get('department_id', '')
            }
        return user_directory
    except FileNotFoundError:
        print(f"Warning: org_structure.json not found at {org_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in org_structure.json at {org_path}")
        return {}

@login_manager.user_loader
def load_user(user_id):
    """Load user from user directory."""
    user_directory = load_user_directory()
    if user_id in user_directory:
        user_data = user_directory[user_id]
        return User(
            user_id=user_id,
            name=user_data.get('name', ''),
            email=user_data.get('email', ''),
            role=user_data.get('role', ''),
            calendar_permissions=user_data.get('calendar_permissions', {})
        )
    return None

def authenticate_user(email, password=None):
    """Simple authentication - check if email exists in user directory."""
    # Load org_structure.json and check email against users
    org_path = Path(__file__).parent.parent.parent / 'shared' / 'database' / 'data-generator' / 'org_structure.json'
    try:
        with open(org_path, 'r') as f:
            org_data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load org_structure.json: {e}")
        return None

    for user in org_data.get('users', []):
        if user.get('email', '').lower() == email.lower():
            # Minimal User object, add more fields if needed
            return User(
                user_id=str(user.get('id', '')),  # Use org_structure id
                name=user.get('name', ''),
                email=user.get('email', ''),
                role=user.get('role_scope', ''),
                calendar_permissions={}  # No calendar_permissions in org_structure
            )
    return None
connected_clients = set()

# Ensure log directory exists
agent_log_file.parent.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_agent_running():
    """Check if the agent process is running."""
    global agent_process
    if agent_process is None:
        return False
    
    try:
        # Check if process is still alive
        if agent_process.poll() is None:
            return True
        else:
            # Process has terminated
            agent_process = None
            return False
    except:
        agent_process = None
        return False

def get_agent_pid():
    """Get the agent process ID."""
    global agent_process
    if agent_process and is_agent_running():
        return agent_process.pid
    return None

def start_agent(user_context=None):
    """Start the calendar agent as a subprocess with real-time output streaming.
    
    Args:
        user_context: Optional dict with user information (id, name, email) to pass to agent
    """
    global agent_process, agent_start_time
    
    if is_agent_running():
        return False, "Agent is already running"
    
    try:
        # Command to start the agent
        agent_script = WORKSHOP_DIR / 'main.py'
        if not agent_script.exists():
            return False, f"Agent script not found: {agent_script}"
        
        # Prepare environment variables including user context if provided
        env = os.environ.copy()
        if user_context and AUTO_INJECT_USER_CONTEXT:
            env['AGENT_USER_ID'] = str(user_context.get('id', ''))
            env['AGENT_USER_NAME'] = user_context.get('name', '')
            env['AGENT_USER_EMAIL'] = user_context.get('email', '')
        
        # Start the agent process with stdout/stderr capture
        agent_process = subprocess.Popen(
            ['python', str(agent_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            cwd=str(WORKSHOP_DIR),
            env=env,
            preexec_fn=os.setsid,  # Create new process group
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        agent_start_time = time.time()
        
        # User context is already passed via environment variables, no need to send via stdin
        
        # Start output streaming
        stream_output_to_clients()
        
        # Give it a moment to start
        time.sleep(1)
        
        if is_agent_running():
            # Notify all connected clients that agent started
            if connected_clients:
                socketio.emit('agent_status', {
                    'running': True,
                    'pid': agent_process.pid,
                    'uptime': 0,
                    'message': f"Agent started successfully (PID: {agent_process.pid})"
                }, namespace='/')
            
            return True, f"Agent started successfully (PID: {agent_process.pid})"
        else:
            return False, "Agent failed to start"
            
    except Exception as e:
        agent_process = None
        return False, f"Failed to start agent: {str(e)}"

def stop_agent():
    """Stop the calendar agent."""
    global agent_process, agent_start_time, output_thread
    
    if not is_agent_running():
        return False, "Agent is not running"
    
    try:
        # Try graceful shutdown first
        os.killpg(os.getpgid(agent_process.pid), signal.SIGTERM)
        
        # Wait up to 5 seconds for graceful shutdown
        for _ in range(50):
            if not is_agent_running():
                break
            time.sleep(0.1)
        
        # Force kill if still running
        if is_agent_running():
            os.killpg(os.getpgid(agent_process.pid), signal.SIGKILL)
            time.sleep(0.5)
        
        agent_process = None
        agent_start_time = None
        output_thread = None
        
        # Notify all connected clients that agent stopped
        if connected_clients:
            socketio.emit('agent_status', {
                'running': False,
                'pid': None,
                'uptime': 0,
                'message': "Agent stopped successfully"
            }, namespace='/')
        
        return True, "Agent stopped successfully"
        
    except Exception as e:
        agent_process = None
        agent_start_time = None
        output_thread = None
        return False, f"Error stopping agent: {str(e)}"

def get_agent_uptime():
    """Get agent uptime in seconds."""
    global agent_start_time
    if agent_start_time and is_agent_running():
        return time.time() - agent_start_time
    return 0

def stream_output_to_clients():
    """Stream agent output to connected WebSocket clients."""
    global agent_process, output_thread
    
    if not agent_process:
        return
    
    def read_output():
        """Read output from agent process and queue it for WebSocket clients."""
        final_response_buffer = []
        capturing_final_response = False
        
        try:
            while agent_process and agent_process.poll() is None:
                line = agent_process.stdout.readline()
                if line:
                    line = line.rstrip()  # Already decoded due to universal_newlines=True
                    agent_output_queue.put(('stdout', line))
                    
                    # Check for final response markers
                    if line == "FINAL_AGENT_RESPONSE_START":
                        capturing_final_response = True
                        final_response_buffer = []
                        continue
                    elif line == "FINAL_AGENT_RESPONSE_END":
                        capturing_final_response = False
                        # Send the captured final response as a special message type
                        if final_response_buffer:
                            final_response_text = '\n'.join(final_response_buffer)
                            if connected_clients:
                                socketio.emit('final_agent_response', {
                                    'message': final_response_text,
                                    'timestamp': time.time()
                                }, namespace='/')
                        continue
                    
                    # If we're capturing the final response, add to buffer instead of emitting
                    if capturing_final_response:
                        final_response_buffer.append(line)
                        continue
                    
                    # For non-final response output, determine output type
                    output_type = 'stdout'
                    if any(keyword in line.lower() for keyword in ['assistant:', 'agent:', 'response:', 'reply:']):
                        output_type = 'agent'
                    
                    # Emit to all connected WebSocket clients (only intermediate output)
                    if connected_clients:
                        socketio.emit('agent_output', {
                            'type': output_type,
                            'data': line,
                            'timestamp': time.time()
                        }, namespace='/')
                else:
                    time.sleep(0.1)
        except Exception as e:
            error_msg = f"Error reading agent output: {str(e)}"
            agent_output_queue.put(('error', error_msg))
            if connected_clients:
                socketio.emit('agent_output', {
                    'type': 'error',
                    'data': error_msg,
                    'timestamp': time.time()
                }, namespace='/')
    
    if output_thread is None or not output_thread.is_alive():
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    global connected_clients
    connected_clients.add(request.sid)
    print(f"Client {request.sid} connected. Total clients: {len(connected_clients)}")
    
    # Send current agent status to new client
    emit('agent_status', {
        'running': is_agent_running(),
        'pid': get_agent_pid(),
        'uptime': get_agent_uptime()
    })
    
    # Removed sending recent logs to avoid replaying old agent output
    # If you want to show logs only when agent is running, you can add a check here
    # ...existing code...

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    global connected_clients
    connected_clients.discard(request.sid)
    print(f"Client {request.sid} disconnected. Total clients: {len(connected_clients)}")

@socketio.on('request_agent_status')
def handle_status_request():
    """Handle status request from client."""
    emit('agent_status', {
        'running': is_agent_running(),
        'pid': get_agent_pid(),
        'uptime': get_agent_uptime()
    })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle message from client to send to agent."""
    global agent_process
    
    # DEBUG: Log all incoming WebSocket messages
    print(f"[DEBUG] WebSocket received message: {data}")
    print(f"[DEBUG] Message content: '{data.get('message', 'NO_MESSAGE_KEY')}'")
    print(f"[DEBUG] Message type: {type(data.get('message'))}")
    print(f"[DEBUG] Message length: {len(data.get('message', ''))}")
    
    # Check if user is authenticated for WebSocket events
    if not current_user.is_authenticated:
        emit('chat_error', {
            'message': 'Please log in to send messages.',
            'timestamp': time.time()
        })
        return
    
    if not is_agent_running():
        emit('chat_error', {
            'message': 'Agent is not running. Please start the agent first.',
            'timestamp': time.time()
        })
        return
    
    try:
        message = data.get('message', '').strip()
        
        # DEBUG: Log message processing
        print(f"[DEBUG] Processing message: '{message}'")
        print(f"[DEBUG] Message empty check: {not message}")
        
        if not message:
            print(f"[DEBUG] Empty message detected, sending error response")
            emit('chat_error', {
                'message': 'Message cannot be empty.',
                'timestamp': time.time()
            })
            return
        
        # Send regular message without runtime context injection
        # (User context is already available via environment variables)
        print(f"[DEBUG] Sending message to agent: '{message}'")
        agent_process.stdin.write(message + '\n')
        
        agent_process.stdin.flush()
        
        # DEBUG: Log the flush operation
        print(f"[DEBUG] Stdin flushed successfully")
        
        # Broadcast the user message to all connected clients (without the context prefix)
        socketio.emit('chat_message', {
            'type': 'user',
            'message': message,
            'timestamp': time.time(),
            'user_name': current_user.name if current_user.is_authenticated else 'Anonymous'
        }, namespace='/')
        
        print(f"Sent message to agent: {message} (from user: {current_user.id if current_user.is_authenticated else 'anonymous'})")
        
    except Exception as e:
        error_msg = f"Error sending message to agent: {str(e)}"
        print(error_msg)
        emit('chat_error', {
            'message': error_msg,
            'timestamp': time.time()
        })

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')  # Optional for now
        
        if not email:
            flash('Please enter an email address.', 'error')
            return render_template('login.html', users=load_user_directory())
        
        user = authenticate_user(email, password)
        if user:
            login_user(user)
            flash(f'Welcome, {user.name}!', 'info')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email address. Please check the available users below.', 'error')
    
    return render_template('login.html', users=load_user_directory())

@app.route('/logout')
@login_required
def logout():
    """Logout and redirect to login page."""
    user_name = current_user.name if current_user.is_authenticated else 'User'
    logout_user()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/test')
def test():
    """Simple test endpoint."""
    return "<h1>Flask is working! 🎉</h1><p>If you see this, the server is running correctly.</p>"

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Calendar Agent Web Interface',
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint with agent information."""
    agent_running = is_agent_running()
    
    status_data = {
        'api': 'active',
        'agent_status': 'running' if agent_running else 'stopped',
        'agent_pid': get_agent_pid(),
        'agent_uptime': get_agent_uptime() if agent_running else 0,
        'calendar_server': 'checking...'  # We'll update this in Stage 3
    }
    
    return jsonify(status_data)

@app.route('/api/agent/start', methods=['POST'])
@login_required
def start_agent_endpoint():
    """Start the calendar agent."""
    # Pass current user context to agent if authenticated
    user_context = None
    if current_user.is_authenticated:
        user_context = {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email
        }
    
    success, message = start_agent(user_context)
    return jsonify({
        'success': success,
        'message': message,
        'agent_running': is_agent_running(),
        'agent_pid': get_agent_pid()
    })

@app.route('/api/agent/stop', methods=['POST'])
@login_required
def stop_agent_endpoint():
    """Stop the calendar agent."""
    success, message = stop_agent()
    return jsonify({
        'success': success,
        'message': message,
        'agent_running': is_agent_running()
    })

@app.route('/api/agent/logs')
def get_agent_logs():
    """Get recent agent logs."""
    try:
        if agent_log_file.exists():
            with open(agent_log_file, 'r') as f:
                logs = f.read()
            # Return last 50 lines
            log_lines = logs.split('\n')
            recent_logs = '\n'.join(log_lines[-50:])
            return jsonify({
                'success': True,
                'logs': recent_logs
            })
        else:
            return jsonify({
                'success': True,
                'logs': 'No logs available yet'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to read logs: {str(e)}"
        })

@app.route('/api/agent/send', methods=['POST'])
@login_required
def send_message_to_agent():
    """Send a message to the running agent."""
    global agent_process
    
    if not is_agent_running():
        return jsonify({
            'success': False,
            'error': 'Agent is not running. Please start the agent first.'
        }), 400
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }, 400)
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }, 400)
        
        # Send message to agent via stdin
        agent_process.stdin.write(message + '\n')
        agent_process.stdin.flush()
        
        # Broadcast the user message to all connected WebSocket clients
        if connected_clients:
            socketio.emit('chat_message', {
                'type': 'user',
                'message': message,
                'timestamp': time.time()
            }, namespace='/')
        
        return jsonify({
            'success': True,
            'message': 'Message sent to agent successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to send message: {str(e)}"
        }), 500

# Calendar Integration Endpoints (Stage 5)

@app.route('/api/calendar/rooms')
def get_rooms():
    """Get list of all available rooms."""
    try:
        rooms_file = WORKSHOP_DIR / 'data' / 'json' / 'rooms.json'
        if rooms_file.exists():
            import json
            with open(rooms_file, 'r') as f:
                rooms_data = json.load(f)
            return jsonify(rooms_data)
        else:
            # Return fallback room data
            return jsonify({
                'rooms': [
                    {
                        'id': 'central-meeting-room-alpha',
                        'name': 'Meeting Room Alpha',
                        'capacity': 10,
                        'room_type': 'meeting_room',
                        'location': 'Main Building, 2nd Floor',
                        'equipment': ['projector', 'whiteboard']
                    },
                    {
                        'id': 'central-meeting-room-beta',
                        'name': 'Meeting Room Beta',
                        'capacity': 8,
                        'room_type': 'meeting_room',
                        'location': 'Main Building, 2nd Floor',
                        'equipment': ['tv_screen', 'whiteboard']
                    },
                    {
                        'id': 'central-lecture-hall-main',
                        'name': 'Main Lecture Hall',
                        'capacity': 200,
                        'room_type': 'lecture_hall',
                        'location': 'Main Building, Ground Floor',
                        'equipment': ['projector', 'microphone', 'speakers']
                    }
                ]
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to load rooms: {str(e)}"
        }), 500

@app.route('/api/calendar/events')
def get_events():
    """Get events within a date range."""
    try:
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        room_id = request.args.get('room_id')
        
        events_file = WORKSHOP_DIR / 'data' / 'json' / 'events.json'
        if events_file.exists():
            import json
            from datetime import datetime
            
            with open(events_file, 'r') as f:
                events_data = json.load(f)
            
            events = events_data.get('events', [])
            
            # Filter by date range if provided
            if start_date and end_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                filtered_events = []
                for event in events:
                    event_start = datetime.fromisoformat(event['start_time'])
                    if start_dt <= event_start <= end_dt:
                        filtered_events.append(event)
                events = filtered_events
            
            # Filter by room if provided
            if room_id:
                events = [event for event in events if event.get('room_id') == room_id]
            
            return jsonify({'events': events})
        else:
            # Return fallback event data
            from datetime import datetime, timedelta
            now = datetime.now()
            return jsonify({
                'events': [
                    {
                        'id': 'demo-1',
                        'title': 'Team Meeting',
                        'start_time': (now + timedelta(hours=2)).isoformat(),
                        'end_time': (now + timedelta(hours=3)).isoformat(),
                        'room_id': 'central-meeting-room-alpha',
                        'organizer': 'Demo User',
                        'status': 'confirmed'
                    },
                    {
                        'id': 'demo-2',
                        'title': 'Project Review',
                        'start_time': (now + timedelta(days=1)).isoformat(),
                        'end_time': (now + timedelta(days=1, hours=1)).isoformat(),
                        'room_id': 'central-meeting-room-beta',
                        'organizer': 'Demo User',
                        'status': 'confirmed'
                    }
                ]
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to load events: {str(e)}"
        }), 500

@app.route('/api/calendar/events', methods=['POST'])
@login_required
def create_event():
    """Create a new calendar event."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Event data is required'
            }), 400
        
        # Validate required fields
        required_fields = ['title', 'room_id', 'start_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f"Missing required field: {field}"
                }), 400
        
        # Calculate end time if duration is provided
        if 'duration_minutes' in data and 'end_time' not in data:
            from datetime import datetime, timedelta
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = start_time + timedelta(minutes=data['duration_minutes'])
            data['end_time'] = end_time.isoformat()
        
        # Generate a unique event ID
        event_id = f"event-{int(time.time())}-{data['room_id'][-4:]}"
        
        # Create the event object
        new_event = {
            'id': event_id,
            'title': data['title'],
            'description': data.get('description', 'Event created via web interface'),
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'room_id': data['room_id'],
            'calendar_id': data['room_id'],
            'organizer': data.get('organizer', 'Web User'),
            'attendee_count': data.get('attendee_count', 1),
            'is_recurring': False,
            'event_type': 'meeting',
            'status': 'confirmed'
        }
        
        # Save to events.json file
        events_file = WORKSHOP_DIR / 'data' / 'json' / 'events.json'
        try:
            if events_file.exists():
                with open(events_file, 'r') as f:
                    events_data = json.load(f)
            else:
                events_data = {'events': []}
            
            # Add the new event
            events_data['events'].append(new_event)
            
            # Save back to file
            with open(events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            # Notify all connected WebSocket clients about the new event
            if connected_clients:
                socketio.emit('calendar_event_created', {
                    'event': new_event,
                    'message': f"New event '{new_event['title']}' created successfully"
                }, namespace='/')
            
            return jsonify({
                'success': True,
                'message': 'Event created successfully',
                'event_id': event_id,
                'event': new_event
            })
            
        except Exception as file_error:
            # Fallback: return success even if file save fails
            logger.warning(f"Could not save event to file: {file_error}")
            return jsonify({
                'success': True,
                'message': 'Event created successfully (in memory only)',
                'event_id': event_id,
                'event': new_event,
                'warning': 'Event not persisted to file'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to create event: {str(e)}"
        }), 500

@app.route('/api/calendar/availability')
def check_availability():
    """Check room availability for a given time slot."""
    try:
        room_id = request.args.get('room_id')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        if not all([room_id, start_time, end_time]):
            return jsonify({
                'success': False,
                'error': 'room_id, start_time, and end_time are required'
            }), 400
        
        # For demonstration, we'll check against existing events
        events_file = WORKSHOP_DIR / 'data' / 'json' / 'events.json'
        if events_file.exists():
            import json
            from datetime import datetime
            
            with open(events_file, 'r') as f:
                events_data = json.load(f)
            
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Check for conflicts
            conflicts = []
            for event in events_data.get('events', []):
                if event.get('room_id') == room_id:
                    event_start = datetime.fromisoformat(event['start_time'])
                    event_end = datetime.fromisoformat(event['end_time'])
                    
                    # Check for overlap
                    if start_dt < event_end and end_dt > event_start:
                        conflicts.append(event)
            
            return jsonify({
                'available': len(conflicts) == 0,
                'conflicts': conflicts
            })
        else:
            # Assume available if no events file
            return jsonify({
                'available': True,
                'conflicts': []
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to check availability: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Calendar Agent Web Interface...")
    print(f"📁 Templates directory: {TEMPLATES_DIR}")
    print(f"📁 Static files directory: {STATIC_DIR}")
    print("🌐 Server will be available at:")
    print("   - http://localhost:8502")
    print("   - http://127.0.0.1:8502")
    print("   - http://0.0.0.0:8502")
    print("✨ WebSocket enabled for real-time output streaming")
    
    # Run with SocketIO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=8502,
        debug=app.config['DEBUG'],
        use_reloader=False,  # Disable reloader to avoid permission issues
        allow_unsafe_werkzeug=True  # For development
    )