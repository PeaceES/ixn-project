# Supabase Database Setup Guide

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign in with GitHub
3. Click "New project"
4. Configure:
   - Organization: Your organization
   - Project name: `ixn-calendar-agent`
   - Database Password: Generate a strong password (save this!)
   - Region: Choose closest to your users
   - Pricing Plan: Free tier

## 2. Run Database Migrations

### Option A: Using Supabase SQL Editor (Recommended)

1. Go to your project dashboard
2. Click "SQL Editor" in the left sidebar
3. Create a new query
4. Copy and paste each file in order:

#### Step 1: Schema
```sql
-- Copy contents of deploy/database/schema.sql
```

#### Step 2: Procedures
```sql
-- Copy contents of deploy/database/procedures.sql
```

#### Step 3: Seed Data
```sql
-- Copy contents of deploy/database/seed.sql
```

5. Run each script by clicking "Run"

### Option B: Using psql Command Line

```bash
# Get connection string from Supabase Settings → Database
export DATABASE_URL="postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres"

# Run migrations
psql $DATABASE_URL -f deploy/database/schema.sql
psql $DATABASE_URL -f deploy/database/procedures.sql
psql $DATABASE_URL -f deploy/database/seed.sql
```

## 3. Get Connection Strings

1. Go to Settings → Database
2. You'll need two connection strings:

### For Direct Connection (Backend Services)
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

### For Connection Pooling (Web Applications)
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
```

## 4. Configure Row Level Security (Optional but Recommended)

1. Go to Authentication → Policies
2. Enable RLS on tables that need it
3. Create policies for your use case

Example policy for calendar.events:
```sql
-- Allow authenticated users to read their own events
CREATE POLICY "Users can view own events" ON calendar.events
FOR SELECT USING (auth.uid() = user_id);
```

## 5. Set Up Database Backups (Recommended)

1. Go to Settings → Backups
2. Configure daily backups (available on free tier)
3. Test restore process periodically

## 6. Monitor Database Usage

Free tier limits:
- 500MB database space
- 2GB bandwidth/month
- 50MB file storage
- Pauses after 1 week of inactivity

Monitor at: Dashboard → Database → Usage

## 7. Connection String Format for Services

Use these environment variables in your services:

### Backend Agent API, Communications Agent, Maintenance Agent
```
SQL_CS=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

### Backend Web Server (with connection pooling)
```
SQL_CS=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
```

## 8. Troubleshooting

### Connection Refused
- Check if project is active (not paused)
- Verify password is correct
- Check IP allowlist settings

### SSL Connection Required
Add `?sslmode=require` to connection string:
```
postgresql://...supabase.com:5432/postgres?sslmode=require
```

### Performance Issues
- Enable connection pooling for web apps
- Use direct connection for long-running agents
- Monitor slow queries in Dashboard → Database → Query Performance

## 9. Production Considerations

Before going to production:
1. Enable Point-in-Time Recovery (paid feature)
2. Set up monitoring alerts
3. Configure custom domain (optional)
4. Review and tighten RLS policies
5. Set up regular backup exports
6. Consider upgrading to Pro plan for:
   - 8GB database
   - No pausing
   - Daily backups to own S3
   - 7-day log retention