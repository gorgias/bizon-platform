# AI Agent

**Priority:** P0
**Effort:** Medium
**Status:** Planned

## Overview

An AI-powered assistant that enables conversational pipeline creation. Users describe what they want in natural language, and the agent creates, configures, and manages pipelines.

## Why This Matters

- **Zero learning curve** - No need to learn YAML syntax or API structure
- **Faster iteration** - Describe changes, agent implements them
- **Error handling** - Agent can diagnose and fix pipeline issues
- **Differentiation** - No other OSS ETL tool has this

## User Experience

```
User: Create a pipeline to sync Stripe customers to BigQuery

Agent: I'll help you create that pipeline. I need a few details:
       1. What's your Stripe API key?
       2. What's your BigQuery project and dataset?

User: API key is sk_live_xxx, project is acme-data, dataset is raw

Agent: I've created the pipeline "stripe-customers-to-bigquery".
       It's currently disabled. Would you like to:
       - Enable it and run now?
       - Set up a schedule (e.g., daily at 2am)?

User: Run it daily at 2am UTC

Agent: Done! Pipeline is scheduled to run daily at 2:00 AM UTC.
       First run will happen tomorrow. You can monitor it at /pipelines/xxx
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      React UI                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Chat Interface                      │   │
│  │  - Message history                               │   │
│  │  - Streaming responses                           │   │
│  │  - Tool call visualization                       │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ SSE Stream
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Service                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   LangGraph  │  │    Tools     │  │ Checkpointer │  │
│  │    Graph     │──│  (Pipeline   │  │  (Postgres)  │  │
│  │              │  │   CRUD, etc) │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Platform API                         │
│         (Pipelines, Connectors, Runs, etc.)            │
└─────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Port Core Agent

1. Copy `agent/` directory from main platform
2. Remove organization context from all tools
3. Simplify state (no multi-tenant user context)
4. Update tool signatures to work without org_id

**Files to port:**
- `agent/main.py` - FastAPI service
- `agent/graph.py` - LangGraph definition
- `agent/state.py` - Agent state (simplified)
- `agent/prompts.py` - System prompts
- `agent/tools/` - All tool implementations

**Tools to simplify:**
| Tool | Changes |
|------|---------|
| `list_pipelines` | Remove org filter |
| `create_pipeline` | Remove org_id assignment |
| `get_pipeline` | Remove org check |
| `trigger_run` | Remove org check |
| `list_connectors` | No changes needed |
| `list_saved_connectors` | Remove org filter |

### Phase 2: Add Chat UI

1. Port `ChatInterface` component from main platform
2. Add SSE streaming support
3. Create `/agent` route in UI
4. Add navigation link

**Components to port:**
- `ChatInterface.tsx`
- `MessageBubble.tsx`
- `useAgentChat.ts` hook

### Phase 3: Configuration

Add settings for LLM provider:

```python
# settings.py
llm_provider: Literal["openai", "anthropic"] = "openai"
llm_model: str = "gpt-4o-mini"
openai_api_key: str | None = None
anthropic_api_key: str | None = None
```

```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxx
```

### Phase 4: Session Management

- Store conversation history in Postgres (LangGraph checkpointer)
- Session ID per browser tab
- Optional: persist sessions for returning users

## API Endpoints

```
POST   /api/agent/chat              # Send message (SSE stream response)
GET    /api/agent/sessions/{id}     # Get session state
DELETE /api/agent/sessions/{id}     # Clear session
GET    /api/agent/health            # Health check
```

## Tool Catalog

### Read-Only Tools
- `list_pipelines` - List all pipelines
- `get_pipeline` - Get pipeline details
- `list_pipeline_runs` - Get run history
- `get_run_status` - Get specific run
- `get_run_logs` - Get execution logs
- `list_sources` - Available source connectors
- `list_destinations` - Available destination connectors
- `list_saved_sources` - Saved source configs
- `list_saved_destinations` - Saved destination configs
- `list_custom_sources` - Custom source connectors

### Write Tools
- `create_pipeline` - Create new pipeline
- `update_pipeline` - Modify pipeline
- `delete_pipeline` - Remove pipeline
- `trigger_run` - Execute pipeline
- `cancel_run` - Stop running pipeline
- `create_saved_source` - Save source config
- `create_saved_destination` - Save destination config

## LLM Requirements

**Recommended models:**
- OpenAI: `gpt-4o-mini` (cost-effective), `gpt-4o` (best quality)
- Anthropic: `claude-3-haiku` (cost-effective), `claude-3-sonnet` (best quality)

**Token usage estimate:**
- System prompt: ~2,000 tokens
- Average conversation: 500-2,000 tokens
- Tool calls: 200-500 tokens each

## Security Considerations

1. **API key exposure** - Agent should never echo back sensitive config values
2. **Rate limiting** - Prevent abuse of LLM API
3. **Input validation** - Sanitize user input before tool calls
4. **Audit logging** - Log all agent actions for debugging

## Testing Strategy

1. **Unit tests** - Tool functions in isolation
2. **Integration tests** - Agent graph with mock LLM
3. **Golden tests** - Expected responses for common scenarios
4. **Manual testing** - Real conversations with various intents

## Success Metrics

- Time to create first pipeline (target: < 2 minutes)
- User satisfaction with agent responses
- Error rate in tool calls
- Conversation completion rate

## Future Enhancements

- **Multi-turn refinement** - "Actually, make it hourly instead"
- **Proactive suggestions** - "I notice this pipeline is failing, want me to check the logs?"
- **Learning from feedback** - Improve based on user corrections
- **Voice interface** - Speech-to-text input
