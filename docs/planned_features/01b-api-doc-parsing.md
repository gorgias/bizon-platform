# Phase 1b: API Documentation Parsing

**Effort:** Medium
**Dependencies:** 01a-core-agent
**PR Size:** ~1 week

## Goal

Reliably extract API structure from various documentation formats. This is the foundation for "connector done right every time" - if we parse wrong, we generate wrong.

## The Challenge

API documentation comes in many forms:

| Format | Quality | Example |
|--------|---------|---------|
| OpenAPI 3.x | Best | Stripe, Twilio |
| Swagger 2.0 | Good | Older APIs |
| HTML docs | Variable | Custom APIs |
| PDF | Poor | Enterprise APIs |
| Nothing | Worst | Internal APIs |

We must handle all of them.

## Parsing Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Input                                                      │
│  (OpenAPI JSON, URL, pasted text, file upload)              │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Format Detection                                           │
│  - Is it valid JSON/YAML?                                   │
│  - Does it have "openapi" or "swagger" key?                 │
│  - Is it a URL?                                             │
│  - Is it raw text?                                          │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  OpenAPI    │   │  URL        │   │  Text/LLM   │
│  Parser     │   │  Fetcher    │   │  Extractor  │
│(deterministic)│  │  + Parser   │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Normalized APISpec                                         │
│  - base_url                                                 │
│  - auth_type, auth_config                                   │
│  - endpoints[]                                              │
│  - pagination_type                                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Human Confirmation                                         │
│  "I found these endpoints. Which do you want?"              │
│  "Authentication looks like API key. Correct?"              │
└─────────────────────────────────────────────────────────────┘
```

## Output: APISpec Model

```python
class AuthConfig(BaseModel):
    type: Literal["api_key", "bearer", "basic", "oauth2", "custom"]
    # For api_key
    key_name: str | None = None  # e.g., "X-API-Key"
    key_location: Literal["header", "query"] | None = None
    # For oauth2
    token_url: str | None = None
    scopes: list[str] | None = None

class Endpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str  # e.g., "/customers"
    description: str | None
    parameters: list[Parameter]
    response_schema: dict | None
    pagination: PaginationConfig | None

class PaginationConfig(BaseModel):
    type: Literal["cursor", "page", "offset", "link_header", "none"]
    cursor_param: str | None  # e.g., "starting_after"
    cursor_path: str | None   # e.g., "data[-1].id"
    page_param: str | None    # e.g., "page"
    limit_param: str | None   # e.g., "limit"
    has_more_path: str | None # e.g., "has_more"

class APISpec(BaseModel):
    name: str
    base_url: str
    auth: AuthConfig
    endpoints: list[Endpoint]
    rate_limit: RateLimitConfig | None
```

## Parsers

### 1. OpenAPI Parser (Deterministic)

```python
def parse_openapi(spec: dict) -> APISpec:
    """
    Parse OpenAPI 3.x or Swagger 2.0 spec.
    Fully deterministic - no LLM needed.
    """
    # Detect version
    if "openapi" in spec:
        return parse_openapi_3(spec)
    elif "swagger" in spec:
        return parse_swagger_2(spec)
    raise ValueError("Unknown spec format")
```

Handles:
- Base URL from `servers` (3.x) or `host`+`basePath` (2.0)
- Auth from `securityDefinitions` / `components.securitySchemes`
- Endpoints from `paths`
- Response schemas from `responses`

### 2. URL Fetcher

```python
async def fetch_api_docs(url: str) -> str:
    """
    Fetch documentation from URL.
    Handles redirects, JS rendering if needed.
    """
    # Try direct fetch first
    response = await fetch(url)

    # Check if it's an OpenAPI spec
    if is_openapi(response.text):
        return response.text

    # Check for common OpenAPI paths
    for path in ["/openapi.json", "/swagger.json", "/api-docs"]:
        spec_url = urljoin(url, path)
        response = await fetch(spec_url)
        if is_openapi(response.text):
            return response.text

    # Return HTML for LLM extraction
    return response.text
```

### 3. LLM Extractor (Fallback)

```python
async def extract_api_spec_with_llm(
    text: str,
    user_context: str | None = None
) -> APISpec:
    """
    Use LLM to extract API structure from unstructured text.
    Only used when OpenAPI spec is not available.
    """
    prompt = f"""
    Extract API specification from this documentation:

    {text}

    User context: {user_context or "None provided"}

    Return JSON matching this schema:
    {APISpec.model_json_schema()}

    If you cannot determine something with confidence,
    set it to null and I will ask the user.
    """

    response = await llm.complete(prompt, response_format=APISpec)
    return response
```

## Human Confirmation Flow

**Never assume - always confirm ambiguous details:**

```
Agent: I parsed your API documentation. Here's what I found:

       Base URL: https://api.example.com/v1
       Auth: API Key in header "X-API-Key"

       Endpoints:
       ☑ GET /customers - List customers
       ☑ GET /orders - List orders
       ☐ GET /internal/metrics - Internal metrics

       Is this correct? Which endpoints do you want to include?

User: Yes, but skip the internal metrics

Agent: Got it. I'll create streams for customers and orders.

       One more thing - I couldn't determine the pagination type.
       How does this API paginate?

       1. Cursor-based (has "next_cursor" or similar)
       2. Page numbers (page=1, page=2)
       3. Offset/limit (offset=0, limit=100)
       4. I'm not sure

User: It uses cursor-based with "starting_after" parameter

Agent: Perfect. I have everything I need to generate the connector.
```

## Tasks

- [ ] Define APISpec pydantic models
- [ ] Implement OpenAPI 3.x parser
- [ ] Implement Swagger 2.0 parser
- [ ] Implement URL fetcher with spec discovery
- [ ] Implement LLM extractor for unstructured docs
- [ ] Create human confirmation flow in chat
- [ ] Add validation for extracted specs
- [ ] Handle edge cases (missing fields, ambiguity)

## Testing

- [ ] Parse Stripe's OpenAPI spec
- [ ] Parse GitHub's OpenAPI spec
- [ ] Parse a Swagger 2.0 spec
- [ ] Extract from plain HTML docs (with LLM)
- [ ] Handle malformed specs gracefully

## Success Criteria

- [ ] 100% success on valid OpenAPI 3.x specs
- [ ] 100% success on valid Swagger 2.0 specs
- [ ] >90% accuracy on HTML docs (with human confirmation)
- [ ] Graceful fallback to asking user when unsure
- [ ] Never generates connector from bad spec data
