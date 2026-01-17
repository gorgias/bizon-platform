# Hosting a Demo Instance

Guide for setting up a public demo instance of Bizon for showcasing features.

## Recommended Setup

**Platform:** Fly.io or Railway
**Why:** Simple deployment, free/cheap tiers, global distribution, easy SSL

## Option 1: Fly.io (Recommended)

### Pros
- Free tier includes Postgres
- Global edge deployment
- Easy scaling
- Built-in SSL

### Setup

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create fly.toml**
   ```toml
   # fly.toml
   app = "bizon-demo"
   primary_region = "iad"  # US East

   [build]
     dockerfile = "Dockerfile"

   [env]
     INSTANCE_NAME = "Bizon Demo"
     INSTANCE_DESCRIPTION = "Try Bizon - Open Source ETL Platform"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0

   [[services]]
     internal_port = 8000
     protocol = "tcp"

     [[services.ports]]
       port = 80
       handlers = ["http"]

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]

   [mounts]
     source = "bizon_data"
     destination = "/data"
   ```

3. **Create Postgres**
   ```bash
   fly postgres create --name bizon-demo-db
   fly postgres attach bizon-demo-db
   ```

4. **Set secrets**
   ```bash
   # Generate encryption key
   fly secrets set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

   # Set demo password
   fly secrets set ADMIN_PASSWORD=demo123

   # Database URL is auto-attached
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Access**
   ```
   https://bizon-demo.fly.dev
   Username: admin (or any)
   Password: demo123
   ```

### Cost
- Free tier: 3 shared VMs, 1GB Postgres
- ~$5-10/month for always-on with small Postgres

---

## Option 2: Railway

### Pros
- One-click deploy from GitHub
- Free tier available
- Simple UI

### Setup

1. **Create railway.json**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     },
     "deploy": {
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. **Deploy via UI**
   - Go to railway.app
   - "New Project" → "Deploy from GitHub repo"
   - Add Postgres plugin
   - Set environment variables

3. **Environment Variables**
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ENCRYPTION_KEY=<generated>
   ADMIN_PASSWORD=demo123
   INSTANCE_NAME=Bizon Demo
   ```

---

## Option 3: Render

### Setup

1. **Create render.yaml**
   ```yaml
   services:
     - type: web
       name: bizon-demo
       env: docker
       plan: free
       envVars:
         - key: DATABASE_URL
           fromDatabase:
             name: bizon-db
             property: connectionString
         - key: ENCRYPTION_KEY
           generateValue: true
         - key: ADMIN_PASSWORD
           value: demo123
         - key: INSTANCE_NAME
           value: Bizon Demo

   databases:
     - name: bizon-db
       plan: free
   ```

2. **Deploy**
   - Connect repo to Render
   - Auto-deploys on push

---

## Demo Mode Features

Consider adding a demo mode that:

### 1. Pre-populated Sample Data

Create seed script for demo:

```python
# scripts/seed_demo.py
DEMO_PIPELINES = [
    {
        "name": "Stripe → BigQuery (Demo)",
        "config": {
            "source": {"name": "dummy", "stream": "customers"},
            "destination": {"name": "logger", "config": {}},
        },
        "schedule": "0 */6 * * *",
        "enabled": True,
    },
    {
        "name": "HubSpot → Snowflake (Demo)",
        "config": {
            "source": {"name": "dummy", "stream": "contacts"},
            "destination": {"name": "logger", "config": {}},
        },
        "schedule": "0 2 * * *",
        "enabled": True,
    },
]

async def seed_demo():
    async with get_db_session() as db:
        for pipeline_data in DEMO_PIPELINES:
            pipeline = Pipeline(**pipeline_data)
            db.add(pipeline)
        await db.commit()
```

### 2. Auto-Reset (Optional)

Reset demo data periodically:

```python
# scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def setup_demo_reset(scheduler: AsyncIOScheduler):
    """Reset demo data every hour."""
    scheduler.add_job(
        reset_demo_data,
        'interval',
        hours=1,
        id='demo_reset',
    )

async def reset_demo_data():
    """Clear and re-seed demo data."""
    async with get_db_session() as db:
        # Delete all runs older than 1 hour
        await db.execute(
            delete(PipelineRun)
            .where(PipelineRun.created_at < datetime.utcnow() - timedelta(hours=1))
        )

        # Reset pipeline configs to defaults
        # ...

        await db.commit()
```

### 3. Read-Only Mode (Optional)

Add setting to prevent destructive operations:

```python
# settings.py
demo_mode: bool = False  # If True, disable delete operations
```

```python
# routes/pipelines.py
@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: uuid.UUID):
    if settings.demo_mode:
        raise HTTPException(403, "Delete is disabled in demo mode")
    # ...
```

### 4. Demo Banner

Add banner to UI in demo mode:

```tsx
// App.tsx
function DemoBanner() {
  if (!import.meta.env.VITE_DEMO_MODE) return null;

  return (
    <div className="bg-yellow-500 text-black text-center py-2">
      This is a demo instance. Data resets hourly.
      <a href="https://github.com/bizon-data/bizon" className="underline ml-2">
        Deploy your own →
      </a>
    </div>
  );
}
```

---

## Monitoring the Demo

### Health Check

```bash
# Fly.io
fly status
fly logs

# Railway
railway logs
```

### Uptime Monitoring

Use free services:
- UptimeRobot (free tier)
- Better Uptime
- Healthchecks.io

```
Monitor: https://bizon-demo.fly.dev/api/health
Interval: 5 minutes
Alert: Email/Slack on failure
```

---

## Cost Summary

| Platform | Free Tier | Recommended |
|----------|-----------|-------------|
| Fly.io | 3 VMs, 1GB Postgres | ~$5-10/mo |
| Railway | 500 hours/mo | ~$5/mo |
| Render | Limited free | ~$7/mo |

---

## Checklist

- [ ] Deploy to chosen platform
- [ ] Set ADMIN_PASSWORD for basic protection
- [ ] Seed with sample pipelines
- [ ] Add demo banner to UI
- [ ] Set up uptime monitoring
- [ ] Add link to demo from README/docs
- [ ] Consider auto-reset for clean state
