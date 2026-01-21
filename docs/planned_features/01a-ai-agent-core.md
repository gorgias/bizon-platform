# AI Agent - Core (Phase 1)

**Priority:** P0
**Effort:** Medium
**Status:** Planned
**Depends on:** Nothing

## Overview

A conversational AI agent with a chat interface that can manage pipelines, discover connectors, and execute runs. This is the foundation that the source generator will build on.

## Goal

Ship a working chat agent that can:
- List, create, update, delete pipelines
- Trigger and monitor pipeline runs
- Discover available sources and destinations
- Manage saved connector configurations

## User Experience

```
User: Show me my pipelines

Agent: You have 3 pipelines:
       1. stripe-to-bigquery (enabled, daily at 2am)
       2. hubspot-contacts (disabled)
       3. postgres-sync (enabled, hourly)

User: Run the stripe pipeline now

Agent: Started stripe-to-bigquery. Run ID: abc123
       Status: Running...

       [2 seconds later]

       Completed! Synced 1,247 records in 8.3s

User: Create a new pipeline from Stripe invoices to BigQuery

Agent: I'll help you create that. Which BigQuery dataset?

User: acme-data.raw

Agent: Created pipeline "stripe-invoices-to-bigquery".
       Want to run it now or set a schedule?
```

## Architecture

```
+-------------------------------------------------------------------+
|                         React UI                                   |
|  +-------------------------------------------------------------+  |
|  |                    Chat Interface                            |  |
|  |  - Message history (markdown rendering)                      |  |
|  |  - SSE streaming for responses                               |  |
|  |  - Code blocks with syntax highlighting                      |  |
|  +-------------------------------------------------------------+  |
+-------------------------------+-----------------------------------+
                                | SSE Stream
                                v
+-------------------------------------------------------------------+
|                      Agent Service                                 |
|  +--------------+  +--------------+  +--------------+             |
|  |   LangGraph  |  |    Tools     |  | Checkpointer |             |
|  |    Graph     |--|  (see below) |  |  (Postgres)  |             |
|  +--------------+  +--------------+  +--------------+             |
+-------------------------------+-----------------------------------+
                                | HTTP (internal)
                                v
+-------------------------------------------------------------------+
|                      Platform API                                  |
|         (Pipelines, Connectors, Runs, Custom Sources)             |
+-------------------------------------------------------------------+
```

## Tool Catalog

### Pipeline Management
| Tool | Description |
|------|-------------|
| `list_pipelines` | List all pipelines with status |
| `get_pipeline` | Get pipeline details and config |
| `create_pipeline` | Create new pipeline |
| `update_pipeline` | Modify pipeline settings |
| `delete_pipeline` | Remove pipeline |

### Run Management
| Tool | Description |
|------|-------------|
| `trigger_run` | Execute pipeline immediately |
| `cancel_run` | Stop running pipeline |
| `list_pipeline_runs` | Get run history |
| `get_run_status` | Get specific run details |
| `get_run_logs` | Get execution logs |

### Connector Discovery
| Tool | Description |
|------|-------------|
| `list_sources` | Available source connectors |
| `list_destinations` | Available destination connectors |
| `get_source_streams` | Get streams for a source |
| `list_saved_sources` | Saved source configurations |
| `list_saved_destinations` | Saved destination configurations |
| `list_custom_sources` | Custom source connectors |

## File Structure

```
bizon_platform_lite/
  agent/
    __init__.py
    main.py                    # FastAPI SSE endpoint
    graph.py                   # LangGraph definition
    state.py                   # Agent state (messages, context)
    prompts.py                 # System prompts
    tools/
      __init__.py
      pipelines.py             # Pipeline CRUD tools
      connectors.py            # Connector discovery tools
      runs.py                  # Run management tools

ui/src/
  pages/AgentPage.tsx          # Chat interface page
  components/agent/
    ChatInterface.tsx          # Main chat component
    MessageBubble.tsx          # Individual message
    CodeBlock.tsx              # Syntax highlighted code
  hooks/
    useAgentChat.ts            # SSE + message handling
  api/
    agent.ts                   # API client
```

## Implementation Tasks

### Backend
- [ ] Create `agent/` module structure
- [ ] Implement LangGraph with ReAct pattern
- [ ] Add Postgres checkpointer for session persistence
- [ ] Implement pipeline tools (CRUD)
- [ ] Implement run tools (trigger, cancel, status, logs)
- [ ] Implement connector discovery tools
- [ ] Create SSE streaming endpoint `/api/agent/chat`
- [ ] Add session management endpoints

### Frontend
- [ ] Create `AgentPage.tsx` with chat layout
- [ ] Implement `ChatInterface.tsx` with message history
- [ ] Add SSE hook for streaming responses
- [ ] Implement markdown rendering in messages
- [ ] Add code block component with syntax highlighting
- [ ] Add navigation link to agent page

### Integration
- [ ] Wire tools to existing platform API endpoints
- [ ] Add LLM provider configuration to settings
- [ ] Create system prompt with platform context
- [ ] Add rate limiting for LLM calls

## API Endpoints

```
POST   /api/agent/chat              # Send message (SSE stream response)
GET    /api/agent/sessions/{id}     # Get session history
DELETE /api/agent/sessions/{id}     # Clear session
GET    /api/agent/health            # Health check
```

### Chat Request/Response

```python
# Request
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # Creates new if not provided

# SSE Events
event: message
data: {"type": "text", "content": "I found 3 pipelines..."}

event: tool_call
data: {"type": "tool_call", "tool": "list_pipelines", "args": {}}

event: tool_result
data: {"type": "tool_result", "tool": "list_pipelines", "result": [...]}

event: done
data: {"session_id": "abc123"}
```

## Settings

```python
# settings.py additions
agent_enabled: bool = True
agent_llm_provider: Literal["openai", "anthropic"] = "anthropic"
agent_llm_model: str = "claude-sonnet-4-20250514"
openai_api_key: str | None = None
anthropic_api_key: str | None = None
```

## System Prompt

```
You are an AI assistant for the Bizon data pipeline platform.

You can help users:
- Create and manage data pipelines
- Configure source and destination connectors
- Trigger and monitor pipeline runs
- View logs and troubleshoot issues

Available sources: {list_sources()}
Available destinations: {list_destinations()}

Be concise and helpful. When creating pipelines, confirm the configuration before saving.
```

## Verification

1. **Unit tests**: Each tool function in isolation
2. **Integration test**: Full conversation with mock LLM
3. **E2E test**: Real conversation in browser
4. **Manual test**: Create pipeline via chat, trigger run, view logs

## Success Criteria

- [ ] Can list pipelines via chat
- [ ] Can create a pipeline with guided conversation
- [ ] Can trigger a run and see status updates
- [ ] Session persists across page refreshes
- [ ] Streaming responses feel responsive

## Next Phase

After this is working, proceed to [01b-ai-agent-source-generator.md](./01b-ai-agent-source-generator.md) to add custom source generation.
