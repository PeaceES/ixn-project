# Complete Step-by-Step Deployment Guide

## Prerequisites Checklist
- [ ] GitHub account with repository created
- [ ] Accounts created on: Supabase, Render, Railway, Vercel
- [ ] Azure AI/OpenAI credentials ready
- [ ] SendGrid account (for email functionality)
- [ ] Git repository pushed to GitHub

## Phase 1: Database Setup (Supabase)

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New project"
3. Fill in:
   - Organization: Select or create one
   - Project name: `ixn-calendar-agent`
   - Database Password: **Generate and save this password!**
   - Region: Choose closest to your users
   - Click "Create new project"
4. Wait for project to initialize (2-3 minutes)

### Step 2: Get Database Connection String
1. In Supabase dashboard, go to Settings (gear icon) → Database
2. Find "Connection string" section
3. Copy the "URI" connection string
4. It looks like: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`
5. Save this - you'll need it for all services

### Step 3: Run Database Migrations
1. In Supabase dashboard, click "SQL Editor" in left sidebar
2. Click "New query"
3. **Run Schema First:**
   - Copy entire contents of `deploy/database/schema.sql`
   - Paste into SQL editor
   - Click "Run" button
   - You should see "Success. No rows returned"
4. **Run Procedures Second:**
   - Click "New query" again
   - Copy entire contents of `deploy/database/procedures.sql`
   - Paste and click "Run"
5. **Run Seed Data Third:**
   - Click "New query" again
   - Copy entire contents of `deploy/database/seed.sql`
   - Paste and click "Run"
6. Verify tables created:
   - Go to "Table Editor" in sidebar
   - You should see tables in the `calendar` schema

## Phase 2: Deploy Backend Services to Render

### Step 4: Deploy Backend Agent API
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect GitHub repository:
   - Click "Connect account" if first time
   - Select your repository
4. Configure service:
   - **Name**: `ixn-backend-agent`
   - **Root Directory**: `deploy/backend-agent`
   - **Environment**: Docker
   - **Plan**: Free
5. Add environment variables (click "Advanced" to expand):
   ```
   PROJECT_CONNECTION_STRING = [your Azure AI connection string]
   MODEL_DEPLOYMENT_NAME = [your model name, e.g., gpt-4]
   AZURE_OPENAI_ENDPOINT = [your Azure OpenAI endpoint]
   AZURE_OPENAI_API_KEY = [your Azure OpenAI API key]
   SQL_CS = [Supabase connection string from Step 2]
   ```
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Save the service URL (e.g., `https://ixn-backend-agent.onrender.com`)

### Step 5: Deploy Communications Agent
1. In Render dashboard, click "New +" → "Web Service"
2. Connect same GitHub repository
3. Configure service:
   - **Name**: `ixn-communications-agent`
   - **Root Directory**: `deploy/communications-agent`
   - **Environment**: Docker
   - **Plan**: Free
4. Add environment variables:
   ```
   PROJECT_CONNECTION_STRING = [same as backend-agent]
   MODEL_DEPLOYMENT_NAME = [same as backend-agent]
   AZURE_OPENAI_ENDPOINT = [same as backend-agent]
   AZURE_OPENAI_API_KEY = [same as backend-agent]
   SQL_CS = [same Supabase connection string]
   SENDGRID_API_KEY = [your SendGrid API key]
   SENDGRID_FROM_EMAIL = noreply@yourdomain.com
   ```
5. Click "Create Web Service"
6. Wait for deployment

### Step 6: Deploy Maintenance Agent
1. In Render dashboard, click "New +" → "Background Worker"
2. Connect same GitHub repository
3. Configure service:
   - **Name**: `ixn-maintenance-agent`
   - **Root Directory**: `deploy/maintenance-agent`
   - **Environment**: Docker
   - **Plan**: Free
4. Add environment variables:
   ```
   PROJECT_CONNECTION_STRING = [same as backend-agent]
   MODEL_DEPLOYMENT_NAME = [same as backend-agent]
   AZURE_OPENAI_ENDPOINT = [same as backend-agent]
   AZURE_OPENAI_API_KEY = [same as backend-agent]
   SQL_CS = [same Supabase connection string]
   MONITOR_INTERVAL_SECONDS = 300
   FAULT_DETECTION_ENABLED = true
   ```
5. Click "Create Background Worker"
6. Wait for deployment

## Phase 3: Deploy Backend Web Server to Railway

### Step 7: Deploy to Railway
1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect GitHub account if needed
5. Select your repository
6. Configure:
   - **Service name**: `backend-web`
   - **Root Directory**: `/deploy/backend-web`
7. Go to Variables tab and add:
   ```
   FLASK_SECRET_KEY = [generate a random secret key]
   FLASK_DEBUG = False
   AGENT_API_URL = [URL from Step 4, e.g., https://ixn-backend-agent.onrender.com]
   SQL_CS = [same Supabase connection string]
   PORT = 8502
   ```
8. Deploy and wait for build
9. In Settings, generate a domain
10. Save the URL (e.g., `https://backend-web.up.railway.app`)

## Phase 4: Deploy Frontend to Vercel

### Step 8: Prepare Frontend Configuration
1. Edit `deploy/frontend/js/config.js`:
   ```javascript
   const CONFIG = {
       WEB_SERVER_URL: 'https://backend-web.up.railway.app',  // Railway URL from Step 7
       WEBSOCKET_URL: 'https://backend-web.up.railway.app',   // Same URL
       API_BASE: '/api',
       ENABLE_DEBUG: false
   };
   ```
2. Commit and push this change to GitHub

### Step 9: Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `deploy/frontend`
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave as is)
5. Click "Deploy"
6. Wait for deployment (1-2 minutes)
7. Save your frontend URL (e.g., `https://ixn-calendar.vercel.app`)

## Phase 5: Set Up CI/CD (Optional but Recommended)

### Step 10: Get Service IDs and Tokens

**Render API Key and Service IDs:**
1. Go to Account Settings in Render
2. Find API Keys section and create one
3. For each service, go to its dashboard
4. The service ID is in URL: `https://dashboard.render.com/web/srv-[SERVICE_ID]`

**Railway Token:**
1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Create new token

**Vercel Tokens:**
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Create token
3. Get project and org IDs:
   ```bash
   cd deploy/frontend
   npx vercel link
   # Follow prompts, this creates .vercel/project.json
   cat .vercel/project.json
   ```

### Step 11: Configure GitHub Secrets
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add these secrets:
   ```
   RENDER_API_KEY = [from Render]
   RENDER_BACKEND_AGENT_SERVICE_ID = srv-[id]
   RENDER_COMMS_AGENT_SERVICE_ID = srv-[id]
   RENDER_MAINT_AGENT_SERVICE_ID = srv-[id]
   RAILWAY_TOKEN = [from Railway]
   VERCEL_TOKEN = [from Vercel]
   VERCEL_ORG_ID = [from vercel link]
   VERCEL_PROJECT_ID = [from vercel link]
   ```

## Phase 6: Testing and Verification

### Step 12: Test Database Connection
1. In Supabase dashboard, go to SQL Editor
2. Run: `SELECT * FROM calendar.users LIMIT 5;`
3. You should see the seeded user data

### Step 13: Test Backend Services
1. **Test Backend Agent API:**
   ```bash
   curl https://ixn-backend-agent.onrender.com/health
   ```
   Should return a health check response

2. **Test Backend Web Server:**
   ```bash
   curl https://backend-web.up.railway.app/api/status
   ```

### Step 14: Test Frontend
1. Open your Vercel URL in browser
2. You should see the login page
3. Try logging in with a test user from seed data

### Step 15: End-to-End Test
1. Open frontend URL
2. Login with demo credentials
3. Start the agent
4. Send a test message like "Show my calendar"
5. Verify agent responds

## Troubleshooting Guide

### Common Issues and Solutions

**Database Connection Failed:**
- Verify connection string format
- Check if Supabase project is active (not paused)
- Ensure password is correct (no special characters issues)

**Render Services Not Starting:**
- Check logs in Render dashboard
- Verify all environment variables are set
- Free tier services sleep after 15 minutes of inactivity

**Railway Deploy Failed:**
- Check build logs
- Verify Python version compatibility
- Ensure requirements.txt is correct

**Frontend Not Connecting:**
- Verify config.js has correct URLs
- Check browser console for errors
- Ensure CORS is properly configured

**Agent Not Responding:**
- Check Azure AI credentials
- Verify model deployment name
- Check service logs for errors

## Post-Deployment Checklist

- [ ] All services deployed and running
- [ ] Database migrations completed
- [ ] Environment variables configured for all services
- [ ] Frontend can connect to backend
- [ ] Agent responds to messages
- [ ] CI/CD pipeline tested (make a commit)
- [ ] Document service URLs for team
- [ ] Set up monitoring/alerts (optional)
- [ ] Configure custom domains (optional)

## Service URLs Reference
Keep these URLs handy:
- **Database**: Supabase Dashboard URL
- **Backend Agent API**: `https://[your-service].onrender.com`
- **Communications Agent**: `https://[your-service].onrender.com`
- **Backend Web**: `https://[your-app].up.railway.app`
- **Frontend**: `https://[your-app].vercel.app`

## Support Resources
- [Supabase Docs](https://supabase.com/docs)
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)