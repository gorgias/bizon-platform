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

Bizon AI is your autonomous data engineer. It manages pipelines, generates connectors, self-heals failures, and collaborates via Git.

The implementation is broken into PR-sized phases:

| Phase | Doc | Effort | Description |
|-------|-----|--------|-------------|
| 1a | [Core Agent](./01a-core-agent.md) | ~1 week | Chat + pipeline management tools |
| 1b | [API Doc Parsing](./01b-api-doc-parsing.md) | ~1 week | Parse OpenAPI, URL, text to structured spec |
| 1c | [Source Generation](./01c-source-generation.md) | ~2 weeks | Templates for auth, pagination, code gen |
| 1d | [Testing Sandbox](./01d-testing-sandbox.md) | ~1 week | Safe execution, real API testing |
| 1e | [Secrets Management](./01e-secrets-management.md) | ~1 week | LLM-safe secrets handling, Vault support |
| 1f | [Self-Healing](./01f-self-healing.md) | ~2 weeks | Auto-diagnose, fix, deploy failed pipelines |

**Key principle: Connector done right every time**

```
┌─────────────────────────────────────────────────────────────┐
│  User provides API docs                                     │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Parse docs (OpenAPI = deterministic, else LLM)             │
│  → Confirm with user if ambiguous                           │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Generate code (80% templates, 20% LLM)                     │
│  → Battle-tested auth/pagination patterns                   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Test in sandbox (real API, secrets never exposed to LLM)   │
│  → Generate → Test → Fix → Repeat until success             │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Working connector                                          │
└─────────────────────────────────────────────────────────────┘
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
