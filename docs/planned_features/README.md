# Bizon Cloud - Product Roadmap

This document outlines the roadmap for Bizon Cloud, the hosted data pipeline platform.

## Product Structure

```
bizon-core        → Open Source (public)   - The ETL engine
Bizon Cloud       → Proprietary (private)  - The hosted platform + AI
```

## Roadmap Overview

| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| P0 | [AI Agent](#ai-agent) | High | Planned |
| P0 | [Webhook Triggers](#webhook-triggers) | Low | Planned |
| P1 | [Pipeline Templates](#pipeline-templates) | Low | Planned |
| P1 | [Observability Dashboard](#observability-dashboard) | Medium | Planned |
| P2 | [CLI Tool](#cli-tool) | Medium | Planned |
| P2 | [Multi-Tenant Architecture](#multi-tenant-architecture) | High | Planned |
| P3 | [Connector Marketplace](#connector-marketplace) | High | Future |

---

## P0 - Critical Path

### AI Agent

**Status:** Planned
**Effort:** High
**Doc:** [01-ai-agent.md](./01-ai-agent.md)

Conversational interface for managing all ETL pipelines. The primary differentiator.

```
User: "Create a pipeline from Stripe to BigQuery, sync daily"
Agent: *creates and configures the pipeline*

User: "I need a connector for my CRM API"
Agent: *generates source, tests it, saves it*
```

### Webhook Triggers

**Status:** Planned
**Effort:** Low
**Doc:** [02-webhook-triggers.md](./02-webhook-triggers.md)

Trigger pipelines via HTTP POST for event-driven architectures.

```bash
curl -X POST https://cloud.bizon.dev/api/pipelines/{id}/webhook \
  -H "X-Webhook-Secret: xxx"
```

---

## P1 - High Value

### Pipeline Templates

**Status:** Planned
**Effort:** Low
**Doc:** [03-pipeline-templates.md](./03-pipeline-templates.md)

Pre-built pipeline configurations for common use cases.

- `stripe-to-bigquery`
- `hubspot-to-snowflake`
- `shopify-to-postgres`

### Observability Dashboard

**Status:** Planned
**Effort:** Medium
**Doc:** [04-observability.md](./04-observability.md)

Production-grade monitoring for pipeline health.

- Run history with filtering
- Success/failure metrics
- Alerting (Slack, email, webhook)

---

## P2 - Scale

### CLI Tool

**Status:** Planned
**Effort:** Medium
**Doc:** [05-cli-tool.md](./05-cli-tool.md)

Command-line interface for power users and CI/CD.

```bash
bizon login
bizon pipelines list
bizon run my-pipeline
```

### Multi-Tenant Architecture

**Status:** Planned
**Effort:** High

Isolated namespaces per customer at scale.

```
┌─────────────────────────────────────────────────────────────┐
│  Bizon Cloud                                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  AI Agent Service (shared)                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐             │
│  │ Client A  │   │ Client B  │   │ Client C  │             │
│  │ namespace │   │ namespace │   │ namespace │             │
│  └───────────┘   └───────────┘   └───────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## P3 - Future

### Connector Marketplace

**Status:** Future
**Effort:** High
**Doc:** [07-connector-marketplace.md](./07-connector-marketplace.md)

Pre-built, maintained connectors for popular APIs.

---

## Pricing Model

| Tier | Price | Included |
|------|-------|----------|
| **Free** | $0 | 3 pipelines, 1K runs/mo, AI included |
| **Pro** | $49/mo | 25 pipelines, unlimited runs, AI included |
| **Team** | $149/mo | Unlimited, 5 seats, priority support |
| **Enterprise** | Custom | Dedicated namespace, SSO, SLA |

AI is included in all tiers. No feature gates.
