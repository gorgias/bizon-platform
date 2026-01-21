# Planned Features

This document outlines the roadmap for Bizon. Features are organized by priority and complexity.

## Roadmap Overview

| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| P0 | [AI Agent Core](#ai-agent-core) | Medium | Planned |
| P0 | [AI Agent Source Generator](#ai-agent-source-generator) | High | Planned |
| P0 | [Webhook Triggers](#webhook-triggers) | Low | Planned |
| P1 | [Pipeline Templates](#pipeline-templates) | Low | Planned |
| P1 | [Observability Dashboard](#observability-dashboard) | Medium | Planned |
| P2 | [CLI Tool](#cli-tool) | Medium | Planned |
| P2 | [GitHub Sync](#github-sync) | Medium | **Implemented** |
| P2 | [AI Agent Monetization](#ai-agent-monetization) | Medium | Planned |
| P3 | [Connector Marketplace](#connector-marketplace) | High | Future |

---

## P0 - Critical Path

### AI Agent Core

**Status:** Planned
**Effort:** Medium
**Doc:** [01a-ai-agent-core.md](./01a-ai-agent-core.md)

Conversational pipeline creation powered by LLM. Chat interface with tools for managing pipelines, runs, and connectors.

```
User: "Create a pipeline from Stripe to BigQuery, sync customers daily"
Agent: *creates and configures the pipeline*
```

### AI Agent Source Generator

**Status:** Planned
**Effort:** High
**Doc:** [01b-ai-agent-source-generator.md](./01b-ai-agent-source-generator.md)
**Depends on:** AI Agent Core

Generate custom source connectors from API documentation. Parse OpenAPI specs, generate code, test against real APIs, fix and retry until working.

```
User: "I need a connector for my CRM API"
Agent: *parses docs, generates source, tests, saves to custom_sources/*
```

### Webhook Triggers

**Status:** Planned
**Effort:** Low (~2 hours)
**Doc:** [02-webhook-triggers.md](./02-webhook-triggers.md)

Trigger pipelines via HTTP POST, enabling event-driven architectures and CI/CD integration.

```bash
curl -X POST https://bizon/api/pipelines/{id}/webhook \
  -H "X-Webhook-Secret: xxx"
```

---

## P1 - High Value

### Pipeline Templates

**Status:** Planned
**Effort:** Low
**Doc:** [03-pipeline-templates.md](./03-pipeline-templates.md)

Pre-built pipeline configurations for common use cases. Copy, paste, customize.

- `stripe-to-bigquery`
- `hubspot-to-snowflake`
- `shopify-to-postgres`
- `github-to-bigquery`

### Observability Dashboard

**Status:** Planned
**Effort:** Medium
**Doc:** [04-observability.md](./04-observability.md)

Production-grade monitoring for pipeline health.

- Run history with filtering
- Success/failure metrics
- Data volume tracking
- Alerting (Slack, email, webhook)

---

## P2 - Developer Experience

### CLI Tool

**Status:** Planned
**Effort:** Medium
**Doc:** [05-cli-tool.md](./05-cli-tool.md)

Command-line interface for local development and CI/CD.

```bash
bizon init                    # Initialize project
bizon source create my_api    # Scaffold custom source
bizon run my-pipeline         # Execute locally
bizon deploy                  # Push to server
```

### GitHub Sync

**Status:** Implemented
**Effort:** Medium (port from main platform)
**Doc:** [06-github-sync.md](./06-github-sync.md)

GitOps workflow for custom sources. Sync custom source code from a git repository on startup. Configure via `GIT_SYNC_*` environment variables.

```
pipelines/
├── stripe-to-bigquery.yaml
├── hubspot-to-snowflake.yaml
└── daily-reports.yaml
```

### AI Agent Monetization

**Status:** Planned
**Effort:** Medium
**Doc:** [01c-ai-agent-monetization.md](./01c-ai-agent-monetization.md)
**Depends on:** AI Agent Source Generator
**Optional:** Yes

Extract source generator as a paid multi-tenant service. Platform calls external API, enabling monetization while keeping platform OSS.

---

## P3 - Future

### Connector Marketplace

**Status:** Future
**Effort:** High
**Doc:** [07-connector-marketplace.md](./07-connector-marketplace.md)

Community-contributed connectors with discovery, rating, and one-click install.

---

## Contributing

Want to work on a feature?

1. Check the feature doc for implementation details
2. Open an issue to discuss approach
3. Submit a PR

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.
