"""
Gunicorn configuration for Flask-SocketIO application
"""

import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8502')}"
backlog = 2048

# Worker processes
workers = 1  # Must be 1 for Flask-SocketIO with eventlet
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'calendar-backend-web'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
keyfile = None
certfile = None