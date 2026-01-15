# Create Custom Source Skill

## Description
Creates a new custom bizon source connector from an API specification or description.

## Usage
```
/create-source <source_name> <api_description>
```

## Instructions

When this skill is invoked, follow these steps:

### 1. Gather Requirements (Use AskUserQuestion Tool)

**IMPORTANT**: Use the `AskUserQuestion` tool to gather information interactively.

**First question - API basics:**
```json
{
  "questions": [
    {
      "question": "What is the base URL of the API?",
      "header": "API URL",
      "options": [
        {"label": "I'll provide it", "description": "Enter the full base URL (e.g., https://api.example.com/v1)"}
      ],
      "multiSelect": false
    },
    {
      "question": "What authentication method does the API use?",
      "header": "Auth",
      "options": [
        {"label": "API Key", "description": "Token passed in header (most common)"},
        {"label": "Bearer Token", "description": "OAuth2 bearer token in Authorization header"},
        {"label": "Basic Auth", "description": "Username and password"},
        {"label": "No Auth", "description": "Public API, no authentication needed"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Second question - Streams and pagination:**
```json
{
  "questions": [
    {
      "question": "What data streams/endpoints should this source support? (comma-separated)",
      "header": "Streams",
      "options": [
        {"label": "I'll list them", "description": "e.g., users, posts, comments"}
      ],
      "multiSelect": false
    },
    {
      "question": "How does the API handle pagination?",
      "header": "Pagination",
      "options": [
        {"label": "Cursor-based", "description": "API returns a cursor/token for next page"},
        {"label": "Page numbers", "description": "Use ?page=1, ?page=2, etc."},
        {"label": "Offset/Limit", "description": "Use ?offset=0&limit=100"},
        {"label": "No pagination", "description": "Returns all data in one request"}
      ],
      "multiSelect": false
    }
  ]
}
```

**If auth requires secrets, ask:**
```json
{
  "questions": [
    {
      "question": "Do you have test API credentials to verify the source works?",
      "header": "Test creds",
      "options": [
        {"label": "Yes, I'll provide", "description": "I have API key/token for testing"},
        {"label": "Skip testing", "description": "Create source without live testing"}
      ],
      "multiSelect": false
    }
  ]
}
```

### 2. Create Source Directory
```bash
mkdir -p custom-sources/{source_name}
```

### 3. Generate source.py

Use this template, adapting to the specific API:

```python
"""
{Source Name} Custom Source

Fetches data from {API description}.
"""

from typing import List, Tuple
from requests.auth import AuthBase
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource

BASE_URL = "{api_base_url}"


class {SourceName}SourceConfig(SourceConfig):
    """Configuration for {source_name} source."""
    pass  # Add custom fields if needed


class {SourceName}Source(AbstractSource):
    """Custom source for {API name}."""

    def __init__(self, config: {SourceName}SourceConfig):
        super().__init__(config)
        self.config: {SourceName}SourceConfig = config

    @staticmethod
    def streams() -> List[str]:
        return [{streams_list}]

    @staticmethod
    def get_config_class() -> type:
        return {SourceName}SourceConfig

    def get_authenticator(self) -> AuthBase | None:
        {auth_implementation}

    def check_connection(self) -> Tuple[bool, str | None]:
        try:
            response = self.session.get(f"{BASE_URL}/{health_endpoint}")
            if response.status_code == 200:
                return True, None
            return False, f"API returned status {response.status_code}"
        except Exception as e:
            return False, str(e)

    def get_total_records_count(self) -> int | None:
        return None  # Implement if API supports count endpoint

    def get(self, pagination: dict = None) -> SourceIteration:
        {pagination_implementation}
```

### 4. Authentication Patterns

**No Auth:**
```python
def get_authenticator(self) -> AuthBase | None:
    return None
```

**API Key (Header):**
```python
from bizon.source.auth.builder import AuthBuilder
from bizon.source.auth.authenticators.token import TokenAuthParams

def get_authenticator(self) -> AuthBase:
    return AuthBuilder.token(
        params=TokenAuthParams(token=self.config.authentication.params.token)
    )
```

**Bearer Token:**
```python
def get_authenticator(self) -> AuthBase:
    class BearerAuth(AuthBase):
        def __init__(self, token):
            self.token = token
        def __call__(self, r):
            r.headers["Authorization"] = f"Bearer {self.token}"
            return r
    return BearerAuth(self.config.authentication.params.token)
```

### 5. Pagination Patterns

**No Pagination (fetch all):**
```python
def get(self, pagination: dict = None) -> SourceIteration:
    if pagination and pagination.get("done"):
        return SourceIteration(next_pagination={}, records=[])

    response = self.session.get(f"{BASE_URL}/{self.config.stream}")
    data = response.json()

    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data
    ]

    return SourceIteration(next_pagination={"done": True}, records=records)
```

**Cursor Pagination:**
```python
def get(self, pagination: dict = None) -> SourceIteration:
    url = f"{BASE_URL}/{self.config.stream}"
    params = {}

    if pagination and pagination.get("cursor"):
        params["cursor"] = pagination["cursor"]

    response = self.session.get(url, params=params)
    data = response.json()

    next_cursor = data.get("next_cursor")
    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data["results"]
    ]

    return SourceIteration(
        next_pagination={"cursor": next_cursor} if next_cursor else {},
        records=records,
    )
```

**Page Number Pagination:**
```python
def get(self, pagination: dict = None) -> SourceIteration:
    page = pagination.get("page", 1) if pagination else 1

    response = self.session.get(
        f"{BASE_URL}/{self.config.stream}",
        params={"page": page, "per_page": 100}
    )
    data = response.json()

    has_more = len(data["items"]) == 100
    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data["items"]
    ]

    return SourceIteration(
        next_pagination={"page": page + 1} if has_more else {},
        records=records,
    )
```

### 6. Test the Source

**IMPORTANT**: Always run this test after creating a source:

```bash
uv run python -c "
from bizon.source.discover import get_external_source_class_by_source_and_stream

source_class = get_external_source_class_by_source_and_stream(
    source_name='{source_name}',
    stream_name='{first_stream}',
    filepath='custom-sources/{source_name}/source.py'
)
print(f'✓ Streams: {source_class.streams()}')

config = source_class.get_config_class()(name='{source_name}', stream='{first_stream}')
source = source_class(config=config)

success, error = source.check_connection()
print(f'✓ Connection: {\"OK\" if success else error}')

result = source.get()
print(f'✓ Records: {len(result.records)}')
if result.records:
    print(f'✓ Sample: {result.records[0].data}')
"
```

### 7. Sample Pipeline Config

```json
{
  "name": "{source_name} to logger",
  "source": {
    "source_file_path": "/custom-sources/{source_name}/source.py",
    "name": "{source_name}",
    "stream": "{first_stream}"
  },
  "destination": {
    "name": "logger",
    "config": {"dummy": "dummy"}
  }
}
```

### 8. Output

After creating the source:
1. Run the test script above
2. If it passes, tell the user:
   - The file path created
   - The test results
   - A sample pipeline config
3. If it fails, debug and fix the issue
