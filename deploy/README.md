# IXN Project - Deployment

This directory contains all the deployment configurations for the Calendar Scheduling Agent system with integrated Communications and Maintenance agents.

## Architecture Overview

The system consists of:
- **PostgreSQL Database** - Hosted on Supabase
- **Backend Agent API** - Calendar scheduling agent (Render)
- **Backend Web Server** - Flask web server with WebSocket support (Railway)
- **Communications Agent** - Email/messaging agent (Render)
- **Maintenance Agent** - Room monitoring and fault detection (Render)
- **Frontend** - Static HTML/JS application (Vercel)

## Quick Start - Local Development

1. **Copy environment template**
   ```bash
   cd deploy
   cp .env.example .env
   # Edit .env with your Azure AI credentials
   ```

2. **Start all services**
   ```bash
   docker-compose up
   ```

3. **Access services**
   - Frontend: http://localhost:3000
   - Web Server: http://localhost:8502
   - Agent API: http://localhost:8000
   - Database: localhost:5432

## Deployment Guides

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide for all services
- [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) - Database setup on Supabase
- [GITHUB_SECRETS.md](./GITHUB_SECRETS.md) - CI/CD configuration
- [AAD_AUTHENTICATION.md](./AAD_AUTHENTICATION.md) - Azure AD setup

## Service Configuration Files

### Backend Agent API
- `backend-agent/Dockerfile` - Docker configuration
- `backend-agent/render.yaml` - Render deployment config
- `backend-agent/.env.example` - Environment template

### Backend Web Server
- `backend-web/Dockerfile` - Docker configuration
- `backend-web/railway.json` - Railway deployment config

### Communications Agent
- `communications-agent/Dockerfile` - Docker configuration
- `communications-agent/render.yaml` - Render deployment config
- `communications-agent/.env.example` - Environment template

### Maintenance Agent
- `maintenance-agent/Dockerfile` - Docker configuration
- `maintenance-agent/render.yaml` - Render deployment config
- `maintenance-agent/.env.example` - Environment template

### Frontend
- `frontend/vercel.json` - Vercel deployment config
- `frontend/js/config.js` - Frontend configuration

## Environment Variables

See `.env.example` for all required environment variables. Key variables include:
- Azure AI credentials (API keys, endpoints)
- Database connection strings
- Service URLs
- SendGrid API credentials (for Communications Agent)

## Testing

Before deploying:
1. Test locally with docker-compose
2. Verify all environment variables are set
3. Check database migrations run successfully
4. Test inter-service communication

## Deployment Checklist

- [ ] Set up Supabase database
- [ ] Configure environment variables for each service
- [ ] Deploy backend-agent to Render
- [ ] Deploy communications-agent to Render
- [ ] Deploy maintenance-agent to Render
- [ ] Deploy backend-web to Railway
- [ ] Deploy frontend to Vercel
- [ ] Configure GitHub secrets for CI/CD
- [ ] Test end-to-end functionality

## Support

For issues or questions:
1. Check service logs in respective dashboards
2. Verify environment variables
3. Test database connectivity
4. Review deployment documentation