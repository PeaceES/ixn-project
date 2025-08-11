"""
Flask Web Server for Calendar Scheduling Agent
Stage 4: Interactive Chat Interface
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
import os
import subprocess
import signal
import psutil
import time
import threading
import queue
from pathlib import Path

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Additional dev container friendly settings
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

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
connected_clients = set()

# Ensure log directory exists
agent_log_file.parent.mkdir(exist_ok=True)

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

def start_agent():
    """Start the calendar agent as a subprocess with real-time output streaming."""
    global agent_process, agent_start_time
    
    if is_agent_running():
        return False, "Agent is already running"
    
    try:
        # Command to start the agent
        agent_script = WORKSHOP_DIR / 'main.py'
        if not agent_script.exists():
            return False, f"Agent script not found: {agent_script}"
        
        # Start the agent process with stdout/stderr capture
        agent_process = subprocess.Popen(
            ['python', str(agent_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            cwd=str(WORKSHOP_DIR),
            preexec_fn=os.setsid,  # Create new process group
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        agent_start_time = time.time()
        
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
        try:
            while agent_process and agent_process.poll() is None:
                line = agent_process.stdout.readline()
                if line:
                    line = line.rstrip()  # Already decoded due to universal_newlines=True
                    agent_output_queue.put(('stdout', line))
                    
                    # Try to detect if this is an agent response vs system output
                    output_type = 'stdout'
                    if any(keyword in line.lower() for keyword in ['assistant:', 'agent:', 'response:', 'reply:']):
                        output_type = 'agent'
                    
                    # Emit to all connected WebSocket clients
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
    
    # Send recent logs if available
    try:
        if agent_log_file.exists():
            with open(agent_log_file, 'r') as f:
                lines = f.readlines()
                # Send last 20 lines to new client
                for line in lines[-20:]:
                    emit('agent_output', {
                        'type': 'stdout',
                        'data': line.rstrip(),
                        'timestamp': time.time()
                    })
    except Exception as e:
        emit('agent_output', {
            'type': 'error',
            'data': f"Error loading recent logs: {str(e)}",
            'timestamp': time.time()
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
    emit('agent_status', {
        'running': is_agent_running(),
        'pid': get_agent_pid(),
        'uptime': get_agent_uptime()
    })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle message from client to send to agent."""
    global agent_process
    
    if not is_agent_running():
        emit('chat_error', {
            'message': 'Agent is not running. Please start the agent first.',
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
        
        # Send message to agent via stdin
        agent_process.stdin.write(message + '\n')
        agent_process.stdin.flush()
        
        # Broadcast the user message to all connected clients
        socketio.emit('chat_message', {
            'type': 'user',
            'message': message,
            'timestamp': time.time()
        }, namespace='/')
        
        print(f"Sent message to agent: {message}")
        
    except Exception as e:
        error_msg = f"Error sending message to agent: {str(e)}"
        print(error_msg)
        emit('chat_error', {
            'message': error_msg,
            'timestamp': time.time()
        })

@app.route('/')
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
def start_agent_endpoint():
    """Start the calendar agent."""
    success, message = start_agent()
    return jsonify({
        'success': success,
        'message': message,
        'agent_running': is_agent_running(),
        'agent_pid': get_agent_pid()
    })

@app.route('/api/agent/stop', methods=['POST'])
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
            }), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
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