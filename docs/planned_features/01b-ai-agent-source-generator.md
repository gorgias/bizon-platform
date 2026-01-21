# AI Agent - Source Generator (Phase 2)

**Priority:** P0
**Effort:** High
**Status:** Planned
**Depends on:** [01a-ai-agent-core.md](./01a-ai-agent-core.md)

## Overview

Extend the AI agent with the ability to generate custom source connectors from API documentation. The agent parses specs, generates Python code, tests against real APIs, and iterates until the code works.

## Core Principle: Can't Fail

The agent doesn't generate code and hope it works. It:
1. Generates initial code from templates + LLM
2. Tests against the real API with user credentials
3. Diagnoses failures
4. Fixes and retries
5. Only succeeds when code actually works with real data

## User Experience

```
User: I want to sync data from my CRM API to BigQuery

Agent: I don't see a built-in connector for that. I can generate one!
       Please provide your API documentation (OpenAPI spec or paste the JSON).

User: {"openapi": "3.0.0", "info": {"title": "MyCRM"}, ...}

Agent: I found 5 endpoints. Which streams do you want to include?
       - GET /customers -> "customers" stream
       - GET /orders -> "orders" stream
       - GET /products -> "products" stream
       - GET /invoices -> "invoices" stream
       - GET /contacts -> "contacts" stream

User: customers and orders

Agent: What authentication does this API use?
       1. API Key (header or query param)
       2. OAuth 2.0
       3. Basic Auth

User: API key in the X-API-Key header

Agent: I need your API key to test the connector. What is it?

User: sk_live_abc123

Agent: Testing connection...

       Connected successfully! Fetched 3 sample customers:
       - {"id": 1, "name": "Acme Corp", ...}
       - {"id": 2, "name": "Globex", ...}

       Saving source as "my-crm"...

       Done! Now let me create the pipeline. What's your BigQuery destination?
```

## Human-in-the-Loop Checkpoints

The agent pauses and asks via chat for:

| Checkpoint | When | What to Ask |
|------------|------|-------------|
| **API Docs** | Start | OpenAPI spec, URL, or description |
| **Stream Selection** | After parsing | Which endpoints to include |
| **Auth Type** | If ambiguous | API key, OAuth, Basic |
| **Credentials** | Before testing | API key, tokens, etc. |
| **Base URL** | If not in spec | Confirm/correct the URL |
| **Retry** | After 3 failures | Continue, manual fix, or abort |

## Architecture

```
                    +------------------+
                    |   Chat Agent     |
                    | (from Phase 1)   |
                    +--------+---------+
                             |
                             | calls source_generator tools
                             v
+----------------------------------------------------------------+
|                    Source Generator Tools                       |
|  +---------------+  +---------------+  +---------------+       |
|  | parse_api_docs|  | generate_code |  | test_source   |       |
|  +---------------+  +---------------+  +---------------+       |
|         |                  |                  |                |
|         v                  v                  v                |
|  +---------------+  +---------------+  +---------------+       |
|  | OpenAPI       |  | Jinja2        |  | Sandbox       |       |
|  | Parser        |  | Templates     |  | Executor      |       |
|  +---------------+  +---------------+  +---------------+       |
|                            |                                   |
|                            v                                   |
|                    +---------------+                           |
|                    | LLM Service   |                           |
|                    | (Claude API)  |                           |
|                    +---------------+                           |
+----------------------------------------------------------------+
```

## Generate -> Test -> Fix Loop

```
parse_api_docs()
       |
       v
+------+------+
| generate()  |<-----------+
+------+------+            |
       |                   |
       v                   |
+------+------+            |
| validate()  |            |
+------+------+            |
       |                   |
       | (syntax ok)       |
       v                   |
+------+------+            |
| test()      |            |
+------+------+            |
       |                   |
       +----> success? ----+
       |         |         |
       |         | yes     | no (attempt < 3)
       |         v         |
       |    save_source()  |
       |                   |
       +----> attempt >= 3?+
                 |
                 v
           ask_user("retry/fix/abort")
```

## Source Generator Tools

### parse_api_docs
```python
def parse_api_docs(spec: str | dict) -> APISpec:
    """
    Parse OpenAPI spec and extract:
    - Base URL
    - Authentication type
    - Endpoints (method, path, description)
    - Response schemas
    """
```

### generate_source_code
```python
def generate_source_code(
    api_spec: APISpec,
    selected_streams: list[str],
    auth_type: str,
    auth_config: dict
) -> str:
    """
    Generate Python source code using:
    1. Base template (Jinja2)
    2. Auth template (token/oauth/basic)
    3. Pagination template (cursor/page/offset)
    4. LLM for custom logic (response parsing, etc.)
    """
```

### validate_source_code
```python
def validate_source_code(code: str) -> ValidationResult:
    """
    Validate generated code:
    1. Syntax check (ast.parse)
    2. Import whitelist (security)
    3. AbstractSource compliance (required methods)
    4. Runtime import test
    """
```

### test_source_connection
```python
def test_source_connection(
    code: str,
    credentials: dict,
    stream: str
) -> TestResult:
    """
    Test the source in a sandbox:
    1. Load code dynamically
    2. Instantiate with credentials
    3. Call check_connection()
    4. Fetch sample records
    5. Return success/failure with details
    """
```

### save_custom_source
```python
def save_custom_source(
    name: str,
    code: str
) -> CustomSource:
    """
    Save to custom_sources/{name}/source.py
    """
```

## File Structure

```
bizon_platform_lite/
  agent/
    tools/
      source_generator/
        __init__.py
        parser.py              # OpenAPI parsing
        generator.py           # Code generation engine
        validator.py           # AST + security checks
        tester.py              # Sandbox execution
        llm_service.py         # Claude API integration
        prompts.py             # Generation/fixing prompts
        templates/
          base_source.py.jinja2
          auth/
            token.py.jinja2
            oauth2.py.jinja2
            basic.py.jinja2
          pagination/
            cursor.py.jinja2
            page.py.jinja2
            offset.py.jinja2
```

## Templates

### base_source.py.jinja2
```python
from typing import List, Tuple
from requests.auth import AuthBase
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource

{{ auth_imports }}

class {{ class_name }}Config(SourceConfig):
    {{ config_fields }}

class {{ class_name }}(AbstractSource):
    def __init__(self, config: {{ class_name }}Config):
        super().__init__(config)
        self.config: {{ class_name }}Config = config
        self.base_url = "{{ base_url }}"

    @staticmethod
    def streams() -> List[str]:
        return {{ streams }}

    @staticmethod
    def get_config_class() -> type:
        return {{ class_name }}Config

    {{ auth_methods }}

    {{ stream_methods }}
```

## LLM Usage

| Task | Approach |
|------|----------|
| OpenAPI parsing | Deterministic (prance/openapi-core) |
| Stream discovery | Deterministic (list GET endpoints) |
| Auth detection | Template match + LLM fallback |
| Pagination detection | LLM (pattern recognition) |
| Response parsing | LLM (generate get() method body) |
| Error fixing | LLM (analyze error, regenerate) |

### Fix Prompt Example
```
The generated source failed with this error:

{error}

Here's the current code:

{code}

Here's the API response we received:

{response}

Please fix the code to handle this response correctly.
```

## Implementation Tasks

### Parser
- [ ] OpenAPI 3.x parser using prance
- [ ] Extract base URL, endpoints, schemas
- [ ] Detect auth type from security schemes
- [ ] Infer pagination from response schemas

### Generator
- [ ] Jinja2 template engine
- [ ] Base source template
- [ ] Auth templates (token, oauth, basic)
- [ ] Pagination templates (cursor, page, offset)
- [ ] LLM integration for custom logic

### Validator
- [ ] Reuse AST validation from validators.py
- [ ] Check AbstractSource compliance
- [ ] Runtime import test
- [ ] Security checks (import whitelist)

### Tester
- [ ] Sandbox execution environment
- [ ] Dynamic code loading
- [ ] Connection test with real credentials
- [ ] Sample record fetching
- [ ] Error capture and formatting

### Integration
- [ ] Wire tools to chat agent
- [ ] Conversational credential collection
- [ ] Generate -> test -> fix loop
- [ ] Save to custom_sources/

## Settings

```python
# Additional settings
agent_max_source_gen_retries: int = 3
agent_source_gen_timeout: int = 30  # seconds per test
```

## Verification

1. **Unit tests**: Parser, generator, validator independently
2. **Integration test**: Full generate -> test -> fix loop with mock API
3. **Real API test**: Generate source for JSONPlaceholder API
4. **E2E test**: Chat -> generate source -> create pipeline

## Test Cases

### JSONPlaceholder (simple)
- No auth, basic pagination
- Should work on first try

### Stripe API (medium)
- Bearer token auth
- Cursor pagination
- Nested response structure

### GitHub API (complex)
- Token auth with custom header
- Link-based pagination
- Rate limiting handling

## Success Criteria

- [ ] Can generate source from OpenAPI spec via chat
- [ ] Tests source against real API
- [ ] Fixes and retries on failure (up to 3x)
- [ ] Saves working source to custom_sources/
- [ ] Continues to create pipeline after source is ready

## Next Phase

After this is working, optionally proceed to [01c-ai-agent-monetization.md](./01c-ai-agent-monetization.md) to extract as a paid service.
