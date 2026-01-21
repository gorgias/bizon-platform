# AI Agent - Monetization (Phase 3)

**Priority:** P2
**Effort:** Medium
**Status:** Planned
**Depends on:** [01b-ai-agent-source-generator.md](./01b-ai-agent-source-generator.md)
**Optional:** Yes - only implement if monetization is a priority

## Overview

Extract the source generator as a separate multi-tenant service that can be offered as a paid API. The open-source platform calls this external service, allowing you to monetize the AI capability while keeping the platform free.

## Why Separate Service?

| Concern | Solution |
|---------|----------|
| **LLM costs** | Metered at API level, passed to user |
| **Moat** | Agent logic is private, can't be forked |
| **Learning loop** | All generations improve the system |
| **Updates** | Ship improvements without platform releases |
| **Self-hosted friendly** | Platform is OSS, agent is optional paid service |

## Architecture

```
+----------------------------------------------------------------------+
|                         USER'S ENVIRONMENT                            |
|  +----------------------------------------------------------------+  |
|  |  Bizon Platform (Open Source)                                  |  |
|  |  - Self-hosted or managed                                      |  |
|  |  - Chat agent calls external API for source generation         |  |
|  +----------------------------------------------------------------+  |
+----------------------------------------------------------------------+
                                    |
                                    | HTTPS API
                                    v
+----------------------------------------------------------------------+
|                      BIZON CLOUD (Your Infrastructure)                |
|  +----------------------------------------------------------------+  |
|  |  AI Agent Service (bizon-agent repo)                           |  |
|  |  +---------------+ +---------------+ +---------------+         |  |
|  |  | API Gateway   | | LangGraph     | | Code Sandbox  |         |  |
|  |  | - Auth        | | - Generation  | | - Test exec   |         |  |
|  |  | - Metering    | | - Retry loop  | | - Validation  |         |  |
|  |  | - Rate limit  | | - State mgmt  | | - Isolation   |         |  |
|  |  +---------------+ +---------------+ +---------------+         |  |
|  |                          |                                     |  |
|  |                          v                                     |  |
|  |  +----------------------------------------------------------+  |  |
|  |  |  LLM Provider (Claude API)                               |  |  |
|  |  +----------------------------------------------------------+  |  |
|  +----------------------------------------------------------------+  |
|                                                                      |
|  +----------------------------------------------------------------+  |
|  |  Shared Services                                               |  |
|  |  - Template library (battle-tested patterns)                   |  |
|  |  - Success/failure telemetry (learning loop)                   |  |
|  |  - Usage database (billing)                                    |  |
|  +----------------------------------------------------------------+  |
+----------------------------------------------------------------------+
```

## Agent Service API

### Start Generation
```
POST /v1/generate/start
Authorization: Bearer <api_key>

{
  "spec": { ... },  // OpenAPI spec
  "options": {
    "auth_type": "token",  // optional hint
    "streams": ["customers", "orders"]  // optional pre-selection
  }
}

Response:
{
  "session_id": "sess_abc123",
  "status": "waiting_for_input",
  "interrupt": {
    "type": "stream_selection",
    "message": "Which streams do you want to include?",
    "options": [
      {"name": "customers", "description": "GET /customers"},
      {"name": "orders", "description": "GET /orders"}
    ]
  }
}
```

### Resume Generation
```
POST /v1/generate/{session_id}/resume
Authorization: Bearer <api_key>

{
  "input": {
    "selected_streams": ["customers", "orders"]
  }
}

Response:
{
  "session_id": "sess_abc123",
  "status": "waiting_for_input",
  "interrupt": {
    "type": "credentials_needed",
    "message": "Please provide API credentials",
    "fields": [
      {"name": "api_key", "type": "password", "required": true}
    ]
  }
}
```

### Get Status
```
GET /v1/generate/{session_id}/status
Authorization: Bearer <api_key>

Response:
{
  "session_id": "sess_abc123",
  "status": "completed",
  "result": {
    "source_code": "...",
    "source_name": "my-crm",
    "streams": ["customers", "orders"],
    "test_results": {
      "success": true,
      "sample_records": 3
    }
  }
}
```

### Cancel
```
POST /v1/generate/{session_id}/cancel
Authorization: Bearer <api_key>
```

## Platform Integration

The chat agent in the OSS platform calls the external service:

```python
# bizon_platform_lite/agent/tools/source_generator/remote.py

import httpx
from bizon_platform_lite.settings import settings

AGENT_API = settings.bizon_agent_api_url  # https://agent.bizon.dev

async def start_generation(spec: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_API}/v1/generate/start",
            headers={"Authorization": f"Bearer {settings.bizon_agent_api_key}"},
            json={"spec": spec}
        )
        return response.json()

async def resume_generation(session_id: str, input: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_API}/v1/generate/{session_id}/resume",
            headers={"Authorization": f"Bearer {settings.bizon_agent_api_key}"},
            json={"input": input}
        )
        return response.json()
```

### Fallback to Local

If no API key is configured, fall back to local generation:

```python
async def generate_source(spec: dict, **kwargs):
    if settings.bizon_agent_api_key:
        return await remote_generate(spec, **kwargs)
    else:
        return await local_generate(spec, **kwargs)
```

## Monetization Model

| Tier | Price | What You Get |
|------|-------|--------------|
| **Free** | $0 | 3 generations/month |
| **Pro** | $29/mo | Unlimited generations, priority queue |
| **Team** | $99/mo | Pro + shared templates, team usage |
| **Enterprise** | Custom | Self-hosted agent, custom models |

## Bizon-Agent Repo Structure

```
bizon-agent/                      # Private repository
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── agent/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app
│   ├── config.py                 # Settings
│   ├── auth.py                   # API key validation
│   ├── metering.py               # Usage tracking
│   ├── graph.py                  # LangGraph definition
│   ├── state.py                  # Session state
│   ├── models.py                 # Pydantic models
│   ├── parsers/
│   │   └── openapi.py
│   ├── generator/
│   │   ├── engine.py
│   │   ├── templates/
│   │   └── llm.py
│   ├── sandbox/
│   │   └── executor.py
│   └── validator.py
├── migrations/                   # Alembic migrations
├── tests/
└── deploy/
    ├── kubernetes/
    └── terraform/
```

## Implementation Tasks

### Service Setup
- [ ] Create bizon-agent repo
- [ ] FastAPI app with async support
- [ ] PostgreSQL for session state
- [ ] Redis for rate limiting
- [ ] Docker + docker-compose

### API Layer
- [ ] API key authentication
- [ ] Rate limiting middleware
- [ ] Usage metering
- [ ] Session management endpoints
- [ ] Webhook for completion notifications (optional)

### Core Logic
- [ ] Port source_generator from platform
- [ ] LangGraph with interrupts
- [ ] Session persistence
- [ ] Tenant isolation

### Security
- [ ] API key rotation
- [ ] Credential pass-through (never stored)
- [ ] Sandbox isolation (containers)
- [ ] Audit logging

### Billing Integration
- [ ] Stripe integration
- [ ] Usage tracking
- [ ] Tier enforcement
- [ ] Upgrade prompts

### Learning Loop
- [ ] Log successful generations
- [ ] Analyze common patterns
- [ ] Improve prompts based on failures
- [ ] Template library from successes

## Platform Settings

```python
# settings.py additions
bizon_agent_api_url: str = "https://agent.bizon.dev"
bizon_agent_api_key: str | None = None  # If set, use remote service
```

## Deployment

### Cloud (Recommended)
- Kubernetes on GCP/AWS
- PostgreSQL (Cloud SQL / RDS)
- Redis (Memorystore / ElastiCache)
- Container execution (Cloud Run / Fargate)

### Self-Hosted Enterprise
- Docker Compose or K8s
- Bring your own LLM API key
- No metering/billing
- Full source access

## Verification

1. **API tests**: All endpoints with mock LLM
2. **Integration test**: Full flow from platform to service
3. **Load test**: Concurrent sessions, rate limiting
4. **Security audit**: Credential handling, isolation

## Success Criteria

- [ ] Platform can use remote service via API key
- [ ] Falls back to local generation if no key
- [ ] Usage is tracked and metered
- [ ] Sessions persist across interrupts
- [ ] Billing integration works

## Future Enhancements

- Pre-built templates for popular APIs (Stripe, HubSpot, etc.)
- Community template marketplace
- "Generate from URL" (fetch and parse docs)
- Learning from successful generations
