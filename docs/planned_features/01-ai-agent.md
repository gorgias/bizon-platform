# Bizon AI - Your Data Engineer

**Priority:** P0
**Effort:** High
**Status:** Planned

## Vision

Bizon AI is an autonomous data engineer that manages your entire data pipeline infrastructure. It doesn't just help you build pipelines - it operates them, monitors them, heals them, and collaborates with you and other AI agents through code.

**Your repo is the shared codebase. Bizon AI is a team member.**

## Implementation Phases

| Phase | Doc | Effort | Description |
|-------|-----|--------|-------------|
| 1a | [Core Agent](./01a-core-agent.md) | ~1 week | Chat UI + pipeline management tools |
| 1b | [API Doc Parsing](./01b-api-doc-parsing.md) | ~1 week | Parse OpenAPI, URL, text → structured APISpec |
| 1c | [Source Generation](./01c-source-generation.md) | ~2 weeks | Templates for auth, pagination, code gen |
| 1d | [Testing Sandbox](./01d-testing-sandbox.md) | ~1 week | Safe execution, real API testing |
| 1e | [Secrets Management](./01e-secrets-management.md) | ~1 week | LLM-safe secrets, Vault/AWS integration |
| 1f | [Self-Healing](./01f-self-healing.md) | ~2 weeks | Auto-diagnose, fix, deploy failed pipelines |

## Core Principle: Connector Done Right Every Time

The AI doesn't guess and hope. It follows a rigorous process:

```
┌─────────────────────────────────────────────────────────────┐
│  1. PARSE                                                   │
│                                                             │
│  OpenAPI spec? → Deterministic parsing (no LLM needed)      │
│  URL/HTML?     → Fetch + LLM extraction                     │
│  Plain text?   → LLM extraction + human confirmation        │
│                                                             │
│  Output: Structured APISpec (endpoints, auth, pagination)   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CONFIRM                                                 │
│                                                             │
│  "I found these endpoints. Which do you need?"              │
│  "Auth looks like API key in header. Correct?"              │
│  "Pagination is cursor-based. Is that right?"               │
│                                                             │
│  Never assume when ambiguous - always ask                   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. GENERATE                                                │
│                                                             │
│  80% templates (battle-tested auth/pagination patterns)     │
│  20% LLM (response parsing, edge cases)                     │
│                                                             │
│  Templates handle the hard parts. LLM fills gaps.           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. TEST                                                    │
│                                                             │
│  Level 1: Syntax check (AST)                                │
│  Level 2: Import check (allowlist)                          │
│  Level 3: Instantiate (no API)                              │
│  Level 4: Connection test (real API)                        │
│  Level 5: Fetch test (real data)                            │
│                                                             │
│  Secrets NEVER exposed to LLM - injected at runtime only    │
└─────────────────────────────────────────────────────────────┘
                         │
                    Pass? ──────────────────┐
                         │                  │
                    No   ▼                  │
┌─────────────────────────────────────────┐ │
│  5. FIX                                 │ │
│                                         │ │
│  Diagnose error (rule-based + LLM)      │ │
│  Apply targeted fix                     │ │
│  Re-test                                │ │
│  Repeat up to 3x                        │ │
└─────────────────────────────────────────┘ │
                         │                  │
                         └──────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────┐
│  WORKING CONNECTOR                                          │
│                                                             │
│  Guaranteed to:                                             │
│  - Authenticate correctly                                   │
│  - Handle pagination                                        │
│  - Fetch real records                                       │
│  - Handle rate limits                                       │
└─────────────────────────────────────────────────────────────┘
```

## Secrets: LLM Never Sees Them

Enterprise customers have strict security policies. Our architecture ensures:

```
┌─────────────────────────────────────────────────────────────┐
│  What LLM sees:                                             │
│                                                             │
│  api_key: ${SECRETS.stripe_key}   ← Reference, not value    │
│                                                             │
│  Test result: "✓ Connected"       ← Outcome, not secrets    │
│  Test result: "401 Unauthorized"  ← Error, secrets redacted │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  What LLM NEVER sees:                                       │
│                                                             │
│  ✗ sk_live_4eC39HqLyjWDarjtT1zdp7dc                         │
│  ✗ Any actual credential value                              │
│  ✗ Secrets in error messages                                │
└─────────────────────────────────────────────────────────────┘

Storage options:
- Encrypted Postgres (default)
- HashiCorp Vault (enterprise)
- AWS Secrets Manager (enterprise)
```

## Self-Healing: Recovers at 3am

```
3:00 AM  Pipeline fails (rate limit exceeded)
3:01 AM  AI diagnoses: "API rate limit hit"
3:02 AM  AI generates fix: add exponential backoff
3:03 AM  AI tests fix: ✓ works
3:04 AM  AI deploys (based on trust level)
3:05 AM  Pipeline recovers

9:00 AM  Engineer sees: "Auto-recovered" status
```

**Trust Levels:**

| Level | Name | Behavior |
|-------|------|----------|
| 1 | Suggest | Opens PR, waits for approval |
| 2 | Assist | Auto-deploys, notifies human |
| 3 | Autonomous | Auto-deploys, logs only |

## Git as Collaboration Layer

```
┌─────────────────────────────────────────────────────────────┐
│  Git Repository (source of truth)                           │
│                                                             │
│  pipelines/                                                 │
│    stripe-to-bigquery.yaml                                  │
│  sources/                                                   │
│    my-crm/source.py                                         │
│  bizon.yaml                                                 │
└─────────────────────────────────────────────────────────────┘
         ▲               ▲               ▲
         │               │               │
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │  Bizon AI │   │  Cursor   │   │  Human    │
   └───────────┘   └───────────┘   └───────────┘

All agents commit to the same repo.
Bizon AI is just another team member.
```

## What Bizon AI Does

### Pipeline Management
```
User: Create a pipeline from Stripe to BigQuery, daily at 2am

AI: Done. Created stripe-to-bq pipeline.
    First run scheduled for 2:00 AM UTC.
```

### Source Generation
```
User: I need a connector for my CRM API

AI: I'll generate that. Share your API docs?

User: [pastes OpenAPI spec]

AI: Testing... ✓ Connected. Fetched 3 sample customers.
    Source saved to sources/my-crm/source.py
```

### Self-Healing
```
AI: Pipeline "hubspot-sync" failed at 3:42 AM.
    Error: API rate limit exceeded.

    I've fixed this by adding backoff.
    [Auto-deployed based on trust level]

    Next run succeeded.
```

### Health Metrics
```
User: How are my pipelines doing?

AI: This week:
    ✓ 142 runs succeeded
    ✗ 3 failures (all auto-recovered)
    📊 2.4M records synced
```

## OSS vs Cloud

| | OSS (Self-Hosted) | Bizon Cloud |
|---|---|---|
| Platform | ✓ | ✓ (hosted) |
| Git sync | ✓ | ✓ |
| Custom sources | ✓ (code yourself) | ✓ (AI generates) |
| **Bizon AI** | ✗ | ✓ |
| Self-healing | ✗ | ✓ |
| Autonomous ops | ✗ | ✓ |

**OSS:** You're the data engineer.
**Cloud:** Bizon AI is your data engineer.
