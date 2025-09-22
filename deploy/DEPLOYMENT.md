# Deployment Guide - Calendar Scheduling Agent

## Overview

This guide walks you through deploying the Calendar Scheduling Agent across multiple free cloud services.

## Architecture

- **Database**: Supabase (PostgreSQL)
- **Backend Agent API**: Render.com
- **Backend Web Server**: Railway.app or Render
- **Communications Agent**: Render.com (Web Service)
- **Maintenance Agent**: Render.com (Background Worker)
- **Frontend**: Vercel or Netlify

## Prerequisites

- GitHub account with your code repository
- Accounts on: Supabase, Render, Railway/Render, Vercel/Netlify
- Azure AI credentials ready

## Step-by-Step Deployment

### 1. Database Setup (Supabase)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Note your database URL and connection string

2. **Run Database Migrations**
   ```bash
   # Connect to Supabase SQL editor and run in order:
   1. deploy/database/schema.sql
   2. deploy/database/procedures.sql
   3. deploy/database/seed.sql
   ```

3. **Get Connection String**
   - Go to Settings → Database
   - Copy the connection string (PostgreSQL format)
   - Format: `postgresql://[user]:[password]@[host]:[port]/[database]`

### 2. Backend Agent API (Render)

1. **Connect GitHub Repository**
   - Go to [render.com](https://render.com)
   - New → Web Service
   - Connect your GitHub repository

2. **Configure Service**
   - Name: `calendar-agent-api`
   - Root Directory: `deploy/backend-agent`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   ```
   PROJECT_CONNECTION_STRING=<your-azure-connection>
   MODEL_DEPLOYMENT_NAME=<your-model-name>
   AZURE_OPENAI_ENDPOINT=<your-endpoint>
   AZURE_OPENAI_API_KEY=<your-api-key>
   SQL_CS=<supabase-connection-string>
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Note your service URL (e.g., `https://calendar-agent-api.onrender.com`)

### 3. Backend Web Server (Railway)

1. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Navigate to backend-web directory
   cd deploy/backend-web
   
   # Initialize and deploy
   railway login
   railway init
   railway up
   ```

2. **Configure via Dashboard**
   - Go to [railway.app](https://railway.app)
   - Select your project
   - Settings → Variables

3. **Add Environment Variables**
   ```
   FLASK_SECRET_KEY=<generate-secure-key>
   FLASK_DEBUG=False
   AGENT_API_URL=https://calendar-agent-api.onrender.com
   SQL_CS=<supabase-connection-string>
   ```

4. **Note Service URL**
   - Your app URL: `https://your-app.up.railway.app`

### 4. Communications Agent (Render)

1. **Connect GitHub Repository**
   - Go to [render.com](https://render.com)
   - New → Web Service
   - Connect your GitHub repository

2. **Configure Service**
   - Name: `communications-agent`
   - Root Directory: `deploy/communications-agent`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

3. **Set Environment Variables**
   ```
   PROJECT_CONNECTION_STRING=<your-azure-connection>
   MODEL_DEPLOYMENT_NAME=<your-model-name>
   AZURE_OPENAI_ENDPOINT=<your-endpoint>
   AZURE_OPENAI_API_KEY=<your-api-key>
   AZURE_CLIENT_ID=<your-client-id>
   AZURE_TENANT_ID=<your-tenant-id>
   AZURE_CLIENT_SECRET=<your-client-secret>
   SQL_CS=<supabase-connection-string>
   SENDGRID_API_KEY=<your-sendgrid-api-key>
   SENDGRID_FROM_EMAIL=<your-from-email>
   USER_DIRECTORY_URL=<optional-user-directory-url>
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Service will run continuously

### 5. Maintenance Agent (Render)

1. **Connect GitHub Repository**
   - Go to [render.com](https://render.com)
   - New → Background Worker
   - Connect your GitHub repository

2. **Configure Service**
   - Name: `maintenance-agent`
   - Root Directory: `deploy/maintenance-agent`
   - Build Command: `apt-get update && apt-get install -y gcc g++ unixodbc-dev && pip install -r requirements.txt`
   - Start Command: `python main.py`

3. **Set Environment Variables**
   ```
   PROJECT_CONNECTION_STRING=<your-azure-connection>
   MODEL_DEPLOYMENT_NAME=<your-model-name>
   AZURE_OPENAI_ENDPOINT=<your-endpoint>
   AZURE_OPENAI_API_KEY=<your-api-key>
   AZURE_CLIENT_ID=<your-client-id>
   AZURE_TENANT_ID=<your-tenant-id>
   AZURE_CLIENT_SECRET=<your-client-secret>
   SQL_CS=<supabase-connection-string>
   MONITOR_INTERVAL_SECONDS=300
   FAULT_DETECTION_ENABLED=true
   ```

4. **Deploy**
   - Click "Create Background Worker"
   - Service will monitor rooms continuously

### 6. Frontend (Vercel)

1. **Prepare for Deployment**
   ```bash
   cd deploy/frontend
   ```

2. **Update Configuration**
   - Edit `js/config.js`:
   ```javascript
   const CONFIG = {
       WEB_SERVER_URL: 'https://your-app.up.railway.app',
       WEBSOCKET_URL: 'https://your-app.up.railway.app',
       API_BASE: '/api',
       ENABLE_DEBUG: false
   };
   ```

3. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Deploy
   vercel --prod
   ```

4. **Set Production URL**
   - Your frontend: `https://your-app.vercel.app`

## Local Development

### Using Docker Compose

1. **Create .env file**
   ```bash
   cd deploy
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Start all services**
   ```bash
   docker-compose up
   ```

3. **Access locally**
   - Frontend: http://localhost:3000
   - Web Server: http://localhost:8502
   - Agent API: http://localhost:8000
   - Database: localhost:5432
   - Communications Agent: Runs in background
   - Maintenance Agent: Runs in background

### Manual Setup

1. **Database**
   ```bash
   # Start PostgreSQL locally
   # Run migration scripts
   ```

2. **Backend Agent**
   ```bash
   cd deploy/backend-agent
   pip install -r requirements.txt
   uvicorn api:app --reload
   ```

3. **Web Server**
   ```bash
   cd deploy/backend-web
   pip install -r requirements.txt
   python web_server.py
   ```

4. **Frontend**
   ```bash
   cd deploy/frontend
   # Use any static server
   python -m http.server 3000
   ```

## Environment Variables Reference

### Backend Agent API
- `PROJECT_CONNECTION_STRING`: Azure AI project connection
- `MODEL_DEPLOYMENT_NAME`: Azure model deployment name
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `SQL_CS`: PostgreSQL connection string

### Backend Web Server
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `FLASK_DEBUG`: Debug mode (False in production)
- `AGENT_API_URL`: URL of deployed agent API
- `SQL_CS`: PostgreSQL connection string

### Communications Agent
- `PROJECT_CONNECTION_STRING`: Azure AI project connection
- `MODEL_DEPLOYMENT_NAME`: Azure model deployment name
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_CLIENT_ID`: Azure AD service principal client ID
- `AZURE_TENANT_ID`: Azure AD tenant ID
- `AZURE_CLIENT_SECRET`: Azure AD client secret
- `SQL_CS`: PostgreSQL connection string
- `SENDGRID_API_KEY`: SendGrid API key for email
- `SENDGRID_FROM_EMAIL`: From email address
- `USER_DIRECTORY_URL`: Optional URL to user directory JSON

### Maintenance Agent
- `PROJECT_CONNECTION_STRING`: Azure AI project connection
- `MODEL_DEPLOYMENT_NAME`: Azure model deployment name
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_CLIENT_ID`: Azure AD service principal client ID
- `AZURE_TENANT_ID`: Azure AD tenant ID
- `AZURE_CLIENT_SECRET`: Azure AD client secret
- `SQL_CS`: PostgreSQL connection string
- `MONITOR_INTERVAL_SECONDS`: Monitoring interval (default: 300)
- `FAULT_DETECTION_ENABLED`: Enable fault detection (default: true)

### Frontend
- Configure in `js/config.js` or via deployment platform

## Testing Deployment

1. **Database Connection**
   ```bash
   # Check if tables are created
   psql $DATABASE_URL -c "\dt calendar.*"
   ```

2. **Agent API Health**
   ```bash
   curl https://your-agent-api.onrender.com/health
   ```

3. **Web Server Status**
   ```bash
   curl https://your-web-server.railway.app/api/status
   ```

4. **Full Integration Test**
   - Open frontend URL
   - Login with demo user
   - Start agent
   - Send test message

## Troubleshooting

### Database Connection Issues
- Verify connection string format
- Check firewall rules in Supabase
- Ensure SSL mode is enabled if required

### Agent Not Responding
- Check Azure credentials
- Verify agent API is running
- Check logs in Render dashboard

### WebSocket Connection Failed
- Ensure web server URL is correct in frontend
- Check CORS settings
- Verify Flask-SocketIO is running

### Frontend Not Loading
- Check browser console for errors
- Verify API URLs in config.js
- Clear browser cache

## Monitoring

### Render Dashboard
- View logs, metrics, and deployments
- Set up health check alerts

### Railway Dashboard
- Monitor resource usage
- View deployment logs

### Supabase Dashboard
- Database metrics
- Query performance
- Storage usage

## Scaling Considerations

### Free Tier Limits
- **Supabase**: 500MB database, 2GB bandwidth
- **Render**: Spins down after 15 min inactivity
- **Railway**: $5 credit/month
- **Vercel**: 100GB bandwidth

### Upgrade Options
- Consider paid tiers for production use
- Add caching layer (Redis)
- Use CDN for static assets
- Implement rate limiting

## Security Notes

- Never commit `.env` files
- Rotate API keys regularly
- Use HTTPS for all services
- Implement proper authentication in production
- Consider adding rate limiting and DDoS protection

## Support

For issues or questions:
1. Check service-specific documentation
2. Review deployment logs
3. Test each component individually
4. Verify environment variables

## Next Steps

After successful deployment:
1. Set up monitoring and alerts
2. Configure custom domains
3. Implement CI/CD pipeline
4. Add error tracking (Sentry)
5. Set up backup strategies