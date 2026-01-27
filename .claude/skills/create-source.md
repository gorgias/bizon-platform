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
        {"label": "API Key (Header)", "description": "Token passed in a custom header (e.g., X-Api-Key)"},
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

### 2. Create Source Directory
```bash
mkdir -p custom_sources/{source_name}
```

### 3. Generate source.py

Use this template, adapting to the specific API:

```python
"""
{Source Name} Custom Source

Fetches data from {API description}.
"""

from typing import List, Tuple

import requests
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource
from requests.auth import AuthBase

BASE_URL = "{api_base_url}"


class {SourceName}SourceConfig(SourceConfig):
    """Configuration for {source_name} source."""
    # Add config fields for secrets - user provides via env vars
    api_key: str  # Set via ${SOURCE_NAME_API_KEY}


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

**API Key (Custom Header):**
```python
def _get_headers(self) -> dict:
    return {
        "Content-Type": "application/json",
        "X-Api-Key": self.config.api_key,
    }
```

**Bearer Token:**
```python
def _get_headers(self) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.config.api_key}",
    }
```

### 5. Pagination Patterns

**No Pagination (fetch all):**
```python
def get(self, pagination: dict = None) -> SourceIteration:
    if pagination and pagination.get("done"):
        return SourceIteration(next_pagination=None, records=[])

    response = requests.get(f"{BASE_URL}/{self.config.stream}", headers=self._get_headers())
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
    params = {}
    if pagination and pagination.get("cursor"):
        params["cursor"] = pagination["cursor"]

    response = requests.get(f"{BASE_URL}/{self.config.stream}", params=params, headers=self._get_headers())
    data = response.json()

    next_cursor = data.get("next_cursor")
    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data["results"]
    ]

    return SourceIteration(
        next_pagination={"cursor": next_cursor} if next_cursor else None,
        records=records,
    )
```

**Offset/Limit Pagination:**
```python
PAGE_SIZE = 100

def get(self, pagination: dict = None) -> SourceIteration:
    offset = pagination.get("offset", 0) if pagination else 0

    response = requests.get(
        f"{BASE_URL}/{self.config.stream}",
        params={"offset": offset, "limit": self.PAGE_SIZE},
        headers=self._get_headers()
    )
    data = response.json()

    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data["items"]
    ]

    next_pagination = None
    if len(data["items"]) == self.PAGE_SIZE:
        next_pagination = {"offset": offset + self.PAGE_SIZE}

    return SourceIteration(next_pagination=next_pagination, records=records)
```

**Page Number Pagination:**
```python
def get(self, pagination: dict = None) -> SourceIteration:
    page = pagination.get("page", 1) if pagination else 1

    response = requests.get(
        f"{BASE_URL}/{self.config.stream}",
        params={"page": page, "per_page": 100},
        headers=self._get_headers()
    )
    data = response.json()

    has_more = len(data["items"]) == 100
    records = [
        SourceRecord(id=str(item["id"]), data=item)
        for item in data["items"]
    ]

    return SourceIteration(
        next_pagination={"page": page + 1} if has_more else None,
        records=records,
    )
```

### 6. Test the Source (Discovery Only)

**IMPORTANT**: First verify the source can be discovered:

```bash
uv run python -c "
from bizon.source.discover import get_external_source_class_by_source_and_stream

source_class = get_external_source_class_by_source_and_stream(
    source_name='{source_name}',
    stream_name='{first_stream}',
    filepath='custom_sources/{source_name}/source.py'
)
print(f'Streams: {source_class.streams()}')
print(f'Config fields: {list(source_class.get_config_class().model_fields.keys())}')
"
```

### 7. Secrets Handling

**CRITICAL: Never ask for actual secret values. Only provide instructions for adding to .env file.**

After creating the source, tell the user:

```
To test the source with your API key:

1. Add your API key to .env:
   echo '{SOURCE_NAME_UPPER}_API_KEY=your_api_key_here' >> .env

2. Test discovery (no API key needed):
   uv run python scripts/test_source.py {source_name} {first_stream}

3. Test with API connection:
   uv run python scripts/test_source.py {source_name} {first_stream} --fetch
```

The test script automatically loads `.env` and maps config fields to environment variables.

### 8. Sample Pipeline Config

```json
{
  "name": "{source_name} to logger",
  "source": {
    "source_file_path": "/custom_sources/{source_name}/source.py",
    "name": "{source_name}",
    "stream": "{first_stream}",
    "config": {
      "api_key": "${SOURCE_NAME_UPPER}_API_KEY}"
    }
  },
  "destination": {
    "name": "logger",
    "config": {"dummy": "dummy"}
  }
}
```

### 9. Output

After creating the source:
1. Run the discovery test to verify the source loads
2. Tell the user:
   - The file path created
   - How to set their API key as an environment variable
   - How to test the connection (after they set the env var)
   - A sample pipeline config with `${SECRET_NAME}` reference
3. **NEVER** ask for or log actual secret values
