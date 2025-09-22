# GitHub Secrets Configuration

Configure these secrets in your GitHub repository for CI/CD deployment.

## Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret below

## Required Secrets

### Render Secrets
- `RENDER_API_KEY`: Your Render API key (from Account Settings)
- `RENDER_BACKEND_AGENT_SERVICE_ID`: Service ID for backend-agent
- `RENDER_COMMS_AGENT_SERVICE_ID`: Service ID for communications-agent
- `RENDER_MAINT_AGENT_SERVICE_ID`: Service ID for maintenance-agent

### Railway Secrets
- `RAILWAY_TOKEN`: Your Railway API token (from Account Settings)

### Vercel Secrets
- `VERCEL_TOKEN`: Your Vercel API token
- `VERCEL_ORG_ID`: Your Vercel organization ID
- `VERCEL_PROJECT_ID`: Your Vercel project ID

## Getting Service IDs

### Render Service IDs
1. Deploy service manually first via Render dashboard
2. Go to service dashboard
3. Service ID is in the URL: `https://dashboard.render.com/web/srv-[SERVICE_ID]`

### Railway Token
1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Create new token
3. Copy and save as `RAILWAY_TOKEN`

### Vercel Tokens
1. Get token from [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Get org and project IDs:
```bash
cd deploy/frontend
npx vercel link
# This creates .vercel/project.json with orgId and projectId
```

## Verify Setup

After adding all secrets:
1. Make a small change to any file
2. Commit and push to main branch
3. Check Actions tab in GitHub
4. Verify all deployment jobs succeed

## Security Notes

- Never commit these secrets to the repository
- Rotate tokens periodically
- Use environment-specific secrets for staging/production
- Restrict secret access to specific branches if needed