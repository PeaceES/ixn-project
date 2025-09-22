# Backend Web Deployment Guide

## Render Deployment Configuration

This Flask application serves as the web interface for the Calendar Scheduling Agent. It connects to the backend-agent API for agent functionality.

### Required Environment Variables

Set these in your Render dashboard under Environment Variables:

1. **AGENT_API_URL** (Required)
   - Value: `https://ixn-backend-agent.onrender.com`
   - Description: URL of your deployed backend-agent service

2. **FLASK_SECRET_KEY** (Auto-generated)
   - Let Render generate this automatically
   - Used for session management

3. **SQL_CS** (Required)
   - Your PostgreSQL connection string
   - Format: `postgresql://user:password@host:port/database`

4. **PORT** (Provided by Render)
   - Automatically set by Render
   - The app will use this port for binding

### Deployment Steps

1. Push changes to your repository
2. Render will automatically rebuild and deploy
3. Check the logs to ensure the Flask server starts correctly
4. Verify the endpoints are accessible:
   - Health check: `https://ixn-web-app.onrender.com/health`
   - API status: `https://ixn-web-app.onrender.com/api/status`

### Architecture

- **Frontend** (Vercel): `https://ixn-project-frontend.vercel.app`
  - Communicates with Backend-Web for UI operations
  
- **Backend-Web** (Render): `https://ixn-web-app.onrender.com`
  - Flask application with WebSocket support
  - Handles authentication, calendar operations
  - Proxies agent requests to Backend-Agent
  
- **Backend-Agent** (Render): `https://ixn-backend-agent.onrender.com`
  - FastAPI application
  - Runs the actual AI agent logic

### Troubleshooting

If you see 404 errors:
- Ensure the Flask app is running (check Render logs)
- Verify CORS is configured correctly
- Check that gunicorn is using eventlet worker

If WebSocket connections fail:
- Ensure eventlet is installed
- Check that only 1 worker is configured (required for Flask-SocketIO)

If agent communication fails:
- Verify AGENT_API_URL is set correctly
- Check that backend-agent service is running