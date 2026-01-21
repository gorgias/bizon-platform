# Phase 1c: Source Generation Templates

**Effort:** High
**Dependencies:** 01b-api-doc-parsing
**PR Size:** ~2 weeks

## Goal

Generate working source connectors from APISpec using battle-tested templates. The templates handle the hard parts (auth, pagination, error handling) so the LLM only fills in API-specific logic.

## Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│  Template (80%)                                             │
│  - Authentication patterns                                  │
│  - Pagination patterns                                      │
│  - Error handling                                           │
│  - Rate limiting                                            │
│  - Retry logic                                              │
│  - Base structure                                           │
└─────────────────────────────────────────────────────────────┘
                         +
┌─────────────────────────────────────────────────────────────┐
│  LLM (20%)                                                  │
│  - Response parsing (extract records from response)         │
│  - Field mapping (if needed)                                │
│  - Custom logic (edge cases)                                │
└─────────────────────────────────────────────────────────────┘
                         =
┌─────────────────────────────────────────────────────────────┐
│  Working Connector                                          │
└─────────────────────────────────────────────────────────────┘
```

**Why templates?**
- Auth and pagination are solved problems
- LLM shouldn't reinvent the wheel
- Tested patterns don't break
- LLM focuses on the unique parts

## Template Library

### Authentication Templates

#### API Key (Header)
```python
# templates/auth/api_key_header.py.jinja2
from requests.auth import AuthBase

class APIKeyAuth(AuthBase):
    def __init__(self, api_key: str, header_name: str = "{{ header_name }}"):
        self.api_key = api_key
        self.header_name = header_name

    def __call__(self, request):
        request.headers[self.header_name] = self.api_key
        return request

def get_authenticator(self) -> AuthBase:
    return APIKeyAuth(
        api_key=self.config.api_key,
        header_name="{{ header_name }}"
    )
```

#### API Key (Query)
```python
# templates/auth/api_key_query.py.jinja2
def get_authenticator(self) -> AuthBase | None:
    return None  # Handled in request params

def _add_auth_params(self, params: dict) -> dict:
    params["{{ param_name }}"] = self.config.api_key
    return params
```

#### Bearer Token
```python
# templates/auth/bearer.py.jinja2
class BearerAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request

def get_authenticator(self) -> AuthBase:
    return BearerAuth(self.config.access_token)
```

#### OAuth2 (Client Credentials)
```python
# templates/auth/oauth2_client_credentials.py.jinja2
class OAuth2ClientCredentials(AuthBase):
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._token = None
        self._token_expires = 0

    def _refresh_token(self):
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 3600) - 60

    def __call__(self, request):
        if not self._token or time.time() > self._token_expires:
            self._refresh_token()
        request.headers["Authorization"] = f"Bearer {self._token}"
        return request
```

### Pagination Templates

#### Cursor-Based
```python
# templates/pagination/cursor.py.jinja2
def get(self, pagination: dict | None = None) -> SourceIteration:
    params = {"limit": {{ page_size }}}

    if pagination and pagination.get("cursor"):
        params["{{ cursor_param }}"] = pagination["cursor"]

    response = self._request("GET", "{{ endpoint }}", params=params)
    data = response.json()

    records = [
        SourceRecord(id=str(r["{{ id_field }}"]), data=r)
        for r in data{{ records_path }}
    ]

    # Determine next cursor
    next_cursor = None
    if data.get("{{ has_more_field }}", False):
        next_cursor = data{{ next_cursor_path }}

    return SourceIteration(
        next_pagination={"cursor": next_cursor} if next_cursor else None,
        records=records
    )
```

#### Page-Based
```python
# templates/pagination/page.py.jinja2
def get(self, pagination: dict | None = None) -> SourceIteration:
    page = pagination.get("page", 1) if pagination else 1

    params = {
        "{{ page_param }}": page,
        "{{ limit_param }}": {{ page_size }}
    }

    response = self._request("GET", "{{ endpoint }}", params=params)
    data = response.json()

    records = [
        SourceRecord(id=str(r["{{ id_field }}"]), data=r)
        for r in data{{ records_path }}
    ]

    # Determine if there's a next page
    total = data.get("{{ total_field }}")
    has_more = len(records) == {{ page_size }}
    if total:
        has_more = page * {{ page_size }} < total

    return SourceIteration(
        next_pagination={"page": page + 1} if has_more else None,
        records=records
    )
```

#### Offset-Based
```python
# templates/pagination/offset.py.jinja2
def get(self, pagination: dict | None = None) -> SourceIteration:
    offset = pagination.get("offset", 0) if pagination else 0

    params = {
        "{{ offset_param }}": offset,
        "{{ limit_param }}": {{ page_size }}
    }

    response = self._request("GET", "{{ endpoint }}", params=params)
    data = response.json()

    records = [
        SourceRecord(id=str(r["{{ id_field }}"]), data=r)
        for r in data{{ records_path }}
    ]

    has_more = len(records) == {{ page_size }}

    return SourceIteration(
        next_pagination={"offset": offset + {{ page_size }}} if has_more else None,
        records=records
    )
```

### Base Template

```python
# templates/base_source.py.jinja2
from typing import List, Tuple
import time
import requests
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
        self.session = requests.Session()

    @staticmethod
    def streams() -> List[str]:
        return {{ streams }}

    @staticmethod
    def get_config_class() -> type:
        return {{ class_name }}Config

    {{ auth_methods }}

    def check_connection(self) -> Tuple[bool, str | None]:
        try:
            auth = self.get_authenticator()
            response = self.session.get(
                f"{self.base_url}{{ health_endpoint }}",
                auth=auth,
                timeout=10
            )
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_total_records_count(self) -> int | None:
        return None  # Unknown

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        **kwargs
    ) -> requests.Response:
        """Make authenticated request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        auth = self.get_authenticator()

        for attempt in range(3):
            try:
                response = self.session.request(
                    method,
                    url,
                    auth=auth,
                    params=params,
                    timeout=30,
                    **kwargs
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        raise RuntimeError("Max retries exceeded")

    {{ get_method }}
```

## Code Generation Flow

```python
def generate_source_code(api_spec: APISpec, streams: list[str]) -> str:
    """Generate source code from API spec."""

    # 1. Select auth template
    auth_template = select_auth_template(api_spec.auth)

    # 2. Select pagination template for each stream
    stream_methods = []
    for stream in streams:
        endpoint = api_spec.get_endpoint(stream)
        pagination_template = select_pagination_template(endpoint.pagination)

        # 3. Use LLM to fill in API-specific details
        get_method = generate_get_method_with_llm(
            endpoint=endpoint,
            pagination_template=pagination_template
        )
        stream_methods.append(get_method)

    # 4. Render base template
    return render_template(
        "base_source.py.jinja2",
        class_name=to_class_name(api_spec.name),
        base_url=api_spec.base_url,
        streams=streams,
        auth_template=auth_template,
        stream_methods=stream_methods,
        config_fields=generate_config_fields(api_spec)
    )
```

## LLM's Role (Limited)

The LLM only helps with:

1. **Response parsing** - Where are the records in the response?
   ```python
   # LLM determines this from the response schema
   records = data["results"]  # or data["data"]["customers"] etc.
   ```

2. **ID field** - What uniquely identifies a record?
   ```python
   # LLM determines this
   id=str(r["id"])  # or r["customer_id"] etc.
   ```

3. **Edge cases** - Any custom logic needed?
   ```python
   # LLM might add
   if r.get("deleted"):
       continue  # Skip deleted records
   ```

## Tasks

- [ ] Create Jinja2 template engine
- [ ] Implement auth templates (api_key, bearer, oauth2, basic)
- [ ] Implement pagination templates (cursor, page, offset, none)
- [ ] Create base source template
- [ ] Build template selector based on APISpec
- [ ] Integrate LLM for response parsing logic
- [ ] Add config field generation
- [ ] Implement code rendering pipeline

## Testing

- [ ] Generate source for Stripe API (cursor pagination, bearer auth)
- [ ] Generate source for GitHub API (page pagination, token auth)
- [ ] Generate source for simple REST API (no pagination, api key)
- [ ] Verify generated code passes AST validation
- [ ] Verify generated code imports correctly

## Success Criteria

- [ ] Generated code follows bizon source contract
- [ ] All auth types work correctly
- [ ] All pagination types work correctly
- [ ] Rate limiting handled automatically
- [ ] Retry logic works for transient failures
- [ ] Code is readable and maintainable
