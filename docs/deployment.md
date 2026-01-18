# Deployment Guide

Guide for deploying Bizon Platform Lite to various cloud platforms.

> **Quick Evaluation**: For trying out Bizon without any setup, use the Gitpod or GitHub Codespaces buttons in the [README](../README.md).

## Recommended Platforms

| Platform | Pros | Cost |
|----------|------|------|
| **Fly.io** | Free Postgres, global edge, easy scaling | Free tier / ~$5-10/mo |
| **Railway** | One-click deploy, simple UI | Free tier / ~$5/mo |
| **Render** | Auto-deploy from GitHub | Free tier / ~$7/mo |

---

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
   app = "bizon-platform"
   primary_region = "iad"  # US East

   [build]
     dockerfile = "Dockerfile"

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
   fly postgres create --name bizon-db
   fly postgres attach bizon-db
   ```

4. **Set secrets**
   ```bash
   # Generate encryption key
   fly secrets set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

   # Optional: Set admin password for basic protection
   fly secrets set ADMIN_PASSWORD=your-secure-password

   # Database URL is auto-attached
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Seed with demo data (optional)**
   ```bash
   fly ssh console -C "python -m bizon_platform_lite.seed"
   ```

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
   - Go to [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub repo"
   - Add Postgres plugin
   - Set environment variables

3. **Environment Variables**
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ENCRYPTION_KEY=<generated>
   ```

---

## Option 3: Render

### Setup

1. **Create render.yaml**
   ```yaml
   services:
     - type: web
       name: bizon-platform
       env: docker
       plan: free
       envVars:
         - key: DATABASE_URL
           fromDatabase:
             name: bizon-db
             property: connectionString
         - key: ENCRYPTION_KEY
           generateValue: true

   databases:
     - name: bizon-db
       plan: free
   ```

2. **Deploy**
   - Connect repo to Render
   - Auto-deploys on push

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `ENCRYPTION_KEY` | Yes | Fernet key for config encryption |
| `ADMIN_PASSWORD` | No | Enables HTTP Basic Auth on all endpoints |
| `STORAGE_LOCAL_PATH` | No | Path for pipeline outputs (default: `/tmp/bizon-outputs`) |
| `CUSTOM_SOURCES_DIR` | No | Path to custom sources (default: `./custom_sources`) |
| `CORS_ALLOWED_ORIGINS` | No | JSON array of allowed origins |

### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Monitoring

### Health Check

All platforms should monitor the health endpoint:
```
GET /api/health
```

### Uptime Monitoring

Recommended free services:
- [UptimeRobot](https://uptimerobot.com) (free tier)
- [Better Uptime](https://betteruptime.com)
- [Healthchecks.io](https://healthchecks.io)

---

## Checklist

- [ ] Deploy to chosen platform
- [ ] Set `ENCRYPTION_KEY` secret
- [ ] Optionally set `ADMIN_PASSWORD` for protection
- [ ] Seed with sample pipelines (`python -m bizon_platform_lite.seed`)
- [ ] Set up uptime monitoring on `/api/health`
- [ ] Test creating and running a pipeline
