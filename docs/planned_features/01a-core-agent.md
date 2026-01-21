# Phase 1a: Core Agent

**Effort:** Medium
**Dependencies:** None
**PR Size:** ~1 week

## Goal

Ship a working chat agent that can manage existing pipelines and connectors. No source generation yet - just conversation over existing platform capabilities.

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Chat UI with SSE streaming | Source generation |
| Pipeline CRUD tools | Self-healing |
| Run management tools | Analytics/charts |
| Connector discovery tools | Git integration |
| Session persistence | Secrets management |

## User Stories

```
User: Show me my pipelines

Agent: You have 3 pipelines:
       1. stripe-to-bigquery (enabled, daily at 2am)
       2. hubspot-contacts (disabled)
       3. postgres-sync (enabled, hourly)

User: Run the stripe pipeline

Agent: Started stripe-to-bigquery. Run ID: run_abc123
       Status: Running...

       Completed! Synced 1,247 records in 8.3s

User: Show me the logs

Agent: [formatted log output]
```

## Implementation

### Backend

```
platform/
  agent/
    __init__.py
    main.py              # FastAPI SSE endpoint
    graph.py             # LangGraph ReAct agent
    state.py             # Conversation state
    prompts.py           # System prompts
    tools/
      __init__.py
      pipelines.py       # list, get, create, update, delete
      runs.py            # trigger, cancel, status, logs
      connectors.py      # list sources, destinations, streams
```

### API

```
POST /api/agent/chat
Content-Type: application/json

{"message": "Show me my pipelines", "session_id": "optional"}

Response: SSE stream
event: message
data: {"content": "You have 3 pipelines..."}

event: done
data: {"session_id": "sess_xxx"}
```

### Frontend

```
ui/src/
  pages/AgentPage.tsx
  components/agent/
    ChatInterface.tsx
    MessageBubble.tsx
    CodeBlock.tsx
  hooks/
    useAgentChat.ts
```

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_pipelines` | List all pipelines | `status?: enabled/disabled` |
| `get_pipeline` | Get pipeline details | `pipeline_id` |
| `create_pipeline` | Create pipeline | `name, source, destination, schedule` |
| `update_pipeline` | Update pipeline | `pipeline_id, updates` |
| `delete_pipeline` | Delete pipeline | `pipeline_id` |
| `trigger_run` | Start pipeline run | `pipeline_id` |
| `get_run_status` | Get run status | `run_id` |
| `get_run_logs` | Get run logs | `run_id` |
| `list_sources` | Available sources | - |
| `list_destinations` | Available destinations | - |
| `get_source_streams` | Streams for a source | `source_name` |

## Tasks

- [ ] Set up agent module structure
- [ ] Implement LangGraph with ReAct pattern
- [ ] Implement pipeline tools
- [ ] Implement run tools
- [ ] Implement connector tools
- [ ] Create SSE streaming endpoint
- [ ] Add session persistence (Postgres)
- [ ] Build chat UI component
- [ ] Add SSE hook for streaming
- [ ] Wire up navigation to /agent

## Testing

- [ ] Unit tests for each tool
- [ ] Integration test: full conversation flow
- [ ] E2E test: create pipeline via chat

## Success Criteria

- [ ] Can list pipelines via chat
- [ ] Can create a pipeline via guided conversation
- [ ] Can trigger a run and see status
- [ ] Sessions persist across page refreshes
- [ ] Streaming responses feel responsive (<500ms first token)
