"""
Flask Web Server for Calendar Scheduling Agent
Modified for remote agent API communication
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit, disconnect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import time
import json
import logging
import httpx
import asyncio
from pathlib import Path
from services.compat_sql_store import get_org_structure, get_user_by_id_or_email

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
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Agent API Configuration
AGENT_API_URL = os.getenv('AGENT_API_URL', 'http://localhost:8000')

# Paths
WORKSHOP_DIR = Path(__file__).parent
STATIC_DIR = WORKSHOP_DIR / 'static'
TEMPLATES_DIR = WORKSHOP_DIR / 'templates'

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
(STATIC_DIR / 'css').mkdir(exist_ok=True)
(STATIC_DIR / 'js').mkdir(exist_ok=True)

# Global variables
connected_clients = set()
agent_initialized = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, name, email, role, calendar_permissions=None):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.calendar_permissions = calendar_permissions or {}

def load_user_directory():
    """Load user directory from database."""
    try:
        org_data = get_org_structure()
        
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
    except Exception as e:
        print(f"Warning: Could not load org structure from database: {e}")
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
    try:
        org_data = get_org_structure()
    except Exception as e:
        print(f"Warning: Could not load org structure from database: {e}")
        return None

    for user in org_data.get('users', []):
        if user.get('email', '').lower() == email.lower():
            return User(
                user_id=str(user.get('id', '')),
                name=user.get('name', ''),
                email=user.get('email', ''),
                role=user.get('role_scope', ''),
                calendar_permissions={}
            )
    return None

# Agent API Communication Functions
async def call_agent_api(endpoint, method='GET', data=None):
    """Call the agent API asynchronously."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{AGENT_API_URL}{endpoint}"
        try:
            if method == 'GET':
                response = await client.get(url)
            elif method == 'POST':
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error calling agent API: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent API HTTP error: {e}")
            raise

def call_agent_api_sync(endpoint, method='GET', data=None):
    """Synchronous wrapper for agent API calls."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(call_agent_api(endpoint, method, data))
    finally:
        loop.close()

def is_agent_running():
    """Check if the agent API is running."""
    try:
        result = call_agent_api_sync('/health')
        return result.get('status') == 'healthy'
    except:
        return False

def get_agent_status():
    """Get the agent status from API."""
    try:
        return call_agent_api_sync('/status')
    except:
        return {
            'status': 'error',
            'agent_initialized': False,
            'mcp_status': None,
            'agent_id': None
        }

def start_agent(user_context=None):
    """Initialize the agent via API."""
    global agent_initialized
    
    try:
        # First check if agent is already initialized
        status = get_agent_status()
        if status.get('agent_initialized'):
            agent_initialized = True
            return True, "Agent is already initialized"
        
        # Initialize the agent
        result = call_agent_api_sync('/initialize', method='POST')
        
        if result.get('success'):
            agent_initialized = True
            
            # Notify all connected clients
            if connected_clients:
                socketio.emit('agent_status', {
                    'running': True,
                    'message': "Agent initialized successfully"
                }, namespace='/')
            
            return True, "Agent initialized successfully"
        else:
            return False, result.get('error', 'Failed to initialize agent')
            
    except Exception as e:
        return False, f"Failed to initialize agent: {str(e)}"

def stop_agent():
    """Reset the agent via API."""
    global agent_initialized
    
    try:
        result = call_agent_api_sync('/reset', method='POST')
        
        if result.get('success'):
            agent_initialized = False
            
            # Notify all connected clients
            if connected_clients:
                socketio.emit('agent_status', {
                    'running': False,
                    'message': "Agent reset successfully"
                }, namespace='/')
            
            return True, "Agent reset successfully"
        else:
            return False, "Failed to reset agent"
            
    except Exception as e:
        return False, f"Error resetting agent: {str(e)}"

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    global connected_clients
    connected_clients.add(request.sid)
    print(f"Client {request.sid} connected. Total clients: {len(connected_clients)}")
    
    # Send current agent status
    status = get_agent_status()
    emit('agent_status', {
        'running': status.get('agent_initialized', False)
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    global connected_clients
    connected_clients.discard(request.sid)
    print(f"Client {request.sid} disconnected. Total clients: {len(connected_clients)}")

@socketio.on('request_agent_status')
def handle_status_request():
    """Handle status request from client."""
    status = get_agent_status()
    emit('agent_status', {
        'running': status.get('agent_initialized', False)
    })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle message from client to send to agent."""
    
    if not current_user.is_authenticated:
        emit('chat_error', {
            'message': 'Please log in to send messages.',
            'timestamp': time.time()
        })
        return
    
    if not agent_initialized:
        emit('chat_error', {
            'message': 'Agent is not initialized. Please start the agent first.',
            'timestamp': time.time()
        })
        return
    
    try:
        message = data.get('message', '').strip()
        
        if not message:
            emit('chat_error', {
                'message': 'Message cannot be empty.',
                'timestamp': time.time()
            })
            return
        
        # Prepare user context
        user_context = {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email
        }
        
        # Call agent API
        result = call_agent_api_sync('/chat', method='POST', data={
            'message': message,
            'user_context': user_context
        })
        
        # Broadcast the user message
        socketio.emit('chat_message', {
            'type': 'user',
            'message': message,
            'timestamp': time.time(),
            'user_name': current_user.name
        }, namespace='/')
        
        # Send agent response
        if result.get('success'):
            socketio.emit('final_agent_response', {
                'message': result.get('response', ''),
                'timestamp': time.time()
            }, namespace='/')
        else:
            emit('chat_error', {
                'message': result.get('error', 'Failed to get response from agent'),
                'timestamp': time.time()
            })
        
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
        password = request.form.get('password')
        
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
    agent_status = get_agent_status()
    
    return jsonify({
        'api': 'active',
        'agent_status': 'running' if agent_status.get('agent_initialized') else 'stopped',
        'calendar_server': 'checking...'
    })

@app.route('/api/agent/start', methods=['POST'])
@login_required
def start_agent_endpoint():
    """Start the calendar agent."""
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
        'agent_running': agent_initialized
    })

@app.route('/api/agent/stop', methods=['POST'])
@login_required
def stop_agent_endpoint():
    """Stop the calendar agent."""
    success, message = stop_agent()
    return jsonify({
        'success': success,
        'message': message,
        'agent_running': agent_initialized
    })

# Calendar Integration Endpoints
@app.route('/api/calendar/rooms')
def get_rooms():
    """Get list of all available rooms from database."""
    try:
        from services.compat_sql_store import get_rooms as sql_get_rooms
        rooms_data = sql_get_rooms()
        return jsonify(rooms_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to load rooms: {str(e)}"
        }), 500

@app.route('/api/calendar/events')
def get_events():
    """Get events within a date range from database."""
    try:
        from datetime import datetime
        from services.compat_sql_store import get_rooms as sql_get_rooms, list_events
        
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        room_id = request.args.get('room_id')
        
        events = []
        if room_id:
            events_data = list_events(room_id)
            events = events_data.get('events', [])
        else:
            rooms_data = sql_get_rooms()
            for room in rooms_data.get('rooms', []):
                room_events = list_events(room['id'])
                events.extend(room_events.get('events', []))
        
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
        
        return jsonify({'events': events})
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
        
        # Generate event ID
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
        
        # Save to database
        from services.compat_sql_store import create_event
        created_event = create_event(new_event)
        
        if created_event:
            # Notify connected clients
            if connected_clients:
                socketio.emit('calendar_event_created', {
                    'event': created_event,
                    'message': f"New event '{created_event['title']}' created successfully"
                }, namespace='/')
            
            return jsonify({
                'success': True,
                'message': 'Event created successfully',
                'event_id': event_id,
                'event': created_event
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create event in database'
            }), 500
            
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
        
        from services.compat_sql_store import check_availability
        is_available = check_availability(room_id, start_time, end_time)
        
        return jsonify({
            'available': is_available,
            'conflicts': [] if is_available else ['Room is not available at this time']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to check availability: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable (Railway provides this)
    port = int(os.getenv('PORT', 8502))
    
    print("🚀 Starting Calendar Agent Web Interface...")
    print(f"📁 Templates directory: {TEMPLATES_DIR}")
    print(f"📁 Static files directory: {STATIC_DIR}")
    print("🌐 Server will be available at:")
    print(f"   - http://0.0.0.0:{port}")
    print("✨ WebSocket enabled for real-time communication")
    print(f"🤖 Agent API URL: {AGENT_API_URL}")
    
    # Run with SocketIO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG'],
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )