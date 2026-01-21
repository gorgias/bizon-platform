# AI Agent

**Priority:** P0
**Effort:** High
**Status:** Planned

## Overview

A conversational AI agent that manages the entire ETL workflow. Users interact via chat to create pipelines, generate custom sources, monitor runs, and troubleshoot issues.

**This is the primary differentiator for Bizon Cloud.**

## User Experience

### Managing Pipelines
```
User: Show me my pipelines

Agent: You have 3 pipelines:
       1. stripe-to-bigquery (enabled, daily at 2am)
       2. hubspot-contacts (disabled)
       3. postgres-sync (enabled, hourly)

User: Run the stripe pipeline now

Agent: Started stripe-to-bigquery. Run ID: abc123

       Completed! Synced 1,247 records in 8.3s
```

### Creating Pipelines
```
User: Create a pipeline from Stripe customers to BigQuery

Agent: I'll set that up. What's your BigQuery project and dataset?

User: acme-data, dataset raw

Agent: Done! Created "stripe-customers-to-bigquery"
       Scheduled daily at 2am. Want to run it now?
```

### Generating Custom Sources
```
User: I need a connector for my company's API

Agent: I can generate that! Paste your API documentation (OpenAPI spec).

User: {"openapi": "3.0.0", "info": {"title": "MyCRM"}, ...}

Agent: Found 4 endpoints. Which streams do you need?
       - /customers
       - /orders
       - /products
       - /invoices

User: customers and orders

Agent: What authentication does this API use?

User: API key in header X-API-Key

Agent: I need your API key to test the connector.

User: sk_live_abc123

Agent: Testing... Connected! Fetched 3 sample records.
       Source saved. Now let me create the pipeline...
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Bizon Cloud                                                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Chat UI                                                  │  │
│  │  - Message history                                        │  │
│  │  - SSE streaming                                          │  │
│  │  - Code blocks                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  AI Agent Service (multi-tenant)                          │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │  LangGraph  │  │   Tools     │  │   LLM       │       │  │
│  │  │  (ReAct)    │──│  (below)    │  │  (Claude)   │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Tenant Namespace                                         │  │
│  │  - Platform instance                                      │  │
│  │  - Pipelines, runs, sources                               │  │
│  │  - Isolated per customer                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Tool Catalog

### Pipeline Management
| Tool | Description |
|------|-------------|
| `list_pipelines` | List all pipelines with status |
| `get_pipeline` | Get pipeline details |
| `create_pipeline` | Create new pipeline |
| `update_pipeline` | Modify pipeline |
| `delete_pipeline` | Remove pipeline |

### Run Management
| Tool | Description |
|------|-------------|
| `trigger_run` | Execute pipeline |
| `cancel_run` | Stop running pipeline |
| `list_runs` | Get run history |
| `get_run_logs` | Get execution logs |

### Connector Discovery
| Tool | Description |
|------|-------------|
| `list_sources` | Available source connectors |
| `list_destinations` | Available destinations |
| `get_source_streams` | Get streams for a source |

### Source Generation
| Tool | Description |
|------|-------------|
| `parse_api_docs` | Extract endpoints from OpenAPI |
| `generate_source` | Create Python connector |
| `test_source` | Test with real credentials |
| `save_source` | Save to tenant's sources |

## Source Generation: Can't Fail

The agent doesn't generate code and hope it works:

```
parse_api_docs()
       │
       ▼
   generate()
       │
       ▼
   validate() ──── syntax error? ──→ fix and retry
       │
       ▼
   test() ──────── API error? ────→ fix and retry (up to 3x)
       │
       ▼
   save()
```

1. Generate initial code from templates + LLM
2. Validate syntax and security
3. Test against real API with user credentials
4. If failure: diagnose, fix, retry
5. Only succeed when code actually works

## Implementation

### File Structure
```
platform/
  agent/
    main.py                    # FastAPI SSE endpoint
    graph.py                   # LangGraph definition
    state.py                   # Conversation state
    prompts.py                 # System prompts
    tools/
      pipelines.py
      runs.py
      connectors.py
      source_generator/
        parser.py              # OpenAPI parsing
        generator.py           # Code generation
        templates/             # Jinja2 templates
        validator.py           # AST + security
        tester.py              # Sandbox execution
```

### API Endpoints
```
POST   /api/agent/chat              # Send message (SSE stream)
GET    /api/agent/sessions/{id}     # Get session history
DELETE /api/agent/sessions/{id}     # Clear session
```

### Multi-Tenant
```python
@app.post("/api/agent/chat")
async def chat(request: ChatRequest, tenant: Tenant = Depends(get_tenant)):
    # Tools scoped to tenant's namespace
    tools = get_tools_for_tenant(tenant.id)
    response = await agent.run(request.message, tools=tools)
    return StreamingResponse(response)
```

## Implementation Phases

### Phase 1: Core Agent
- [ ] LangGraph setup with ReAct pattern
- [ ] Pipeline tools (CRUD)
- [ ] Run tools (trigger, status, logs)
- [ ] Connector discovery tools
- [ ] Chat UI with SSE streaming
- [ ] Session persistence

### Phase 2: Source Generator
- [ ] OpenAPI parser
- [ ] Jinja2 templates (auth, pagination)
- [ ] LLM integration for custom logic
- [ ] Sandbox for testing
- [ ] Generate → test → fix loop

### Phase 3: Production
- [ ] Multi-tenant isolation
- [ ] Rate limiting
- [ ] Error handling
- [ ] Telemetry / logging

## Success Metrics

- Time to create first pipeline (target: < 2 min)
- Source generation success rate (target: > 90%)
- User retention after first AI interaction
