# Planned Features

This document outlines the roadmap for Bizon. Features are organized by priority and complexity.

## Roadmap Overview

| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| P0 | [AI Agent](#ai-agent) | Medium | Planned |
| P0 | [Webhook Triggers](#webhook-triggers) | Low | Planned |
| P1 | [Pipeline Templates](#pipeline-templates) | Low | Planned |
| P1 | [Observability Dashboard](#observability-dashboard) | Medium | Planned |
| P2 | [CLI Tool](#cli-tool) | Medium | Planned |
| P2 | [GitHub Sync](#github-sync) | Medium | Planned |
| P3 | [Connector Marketplace](#connector-marketplace) | High | Future |

---

## P0 - Critical Path

### AI Agent

**Status:** Planned
**Effort:** Medium (port from main platform)
**Doc:** [01-ai-agent.md](./01-ai-agent.md)

Conversational pipeline creation powered by LLM. The killer feature that differentiates Bizon from every other ETL tool.

```
User: "Create a pipeline from Stripe to BigQuery, sync customers daily"
Agent: *creates and configures the pipeline*
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

**Status:** Planned
**Effort:** Medium (port from main platform)
**Doc:** [06-github-sync.md](./06-github-sync.md)

GitOps workflow for pipeline management. Define pipelines as YAML in git, sync automatically.

```
pipelines/
├── stripe-to-bigquery.yaml
├── hubspot-to-snowflake.yaml
└── daily-reports.yaml
```

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
