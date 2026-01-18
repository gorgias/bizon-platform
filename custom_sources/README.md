# Custom Sources

Custom sources let you create your own data connectors by writing Python code that extends `AbstractSource` from the bizon library.

## Quick Start

1. Create a folder for your source in `custom_sources/`
2. Create a `source.py` file with your source class
3. Reference it in your pipeline config with `source_file_path`

## Example: JSONPlaceholder Source

See `jsonplaceholder/source.py` for a complete working example.

### Pipeline Config

```json
{
  "name": "jsonplaceholder to logger",
  "source": {
    "source_file_path": "/custom_sources/jsonplaceholder/source.py",
    "name": "jsonplaceholder",
    "stream": "posts"
  },
  "destination": {
    "name": "logger",
    "config": {"dummy": "dummy"}
  }
}
```

## Creating a Custom Source

### Required Structure

```python
from typing import List, Tuple
from requests.auth import AuthBase
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource


class MySourceConfig(SourceConfig):
    """Add any custom config fields here."""
    api_key: str  # Example custom field


class MySource(AbstractSource):
    """Your custom source implementation."""

    @staticmethod
    def streams() -> List[str]:
        """Return list of available streams."""
        return ["stream1", "stream2"]

    @staticmethod
    def get_config_class() -> type:
        """Return config class."""
        return MySourceConfig

    def get_authenticator(self) -> AuthBase | None:
        """Return authenticator or None."""
        return None

    def check_connection(self) -> Tuple[bool, str | None]:
        """Test connectivity. Return (success, error_message)."""
        return True, None

    def get_total_records_count(self) -> int | None:
        """Return total records if known, else None."""
        return None

    def get(self, pagination: dict = None) -> SourceIteration:
        """Fetch records. Called repeatedly until next_pagination is empty."""
        # Your fetch logic here
        return SourceIteration(
            next_pagination={},  # Empty = no more pages
            records=[
                SourceRecord(id="1", data={"key": "value"})
            ]
        )
```

### Key Concepts

#### Pagination

The `get()` method is called repeatedly until `next_pagination` is empty:

```python
def get(self, pagination: dict = None) -> SourceIteration:
    if pagination is None:
        # First call - fetch first page
        page = 1
    else:
        # Subsequent calls - use pagination state
        page = pagination.get("page", 1)

    # Fetch data...
    data = fetch_page(page)
    has_more = len(data) == PAGE_SIZE

    return SourceIteration(
        next_pagination={"page": page + 1} if has_more else {},
        records=[SourceRecord(id=str(r["id"]), data=r) for r in data]
    )
```

#### Authentication

Use the built-in auth builders:

```python
from bizon.source.auth.builder import AuthBuilder
from bizon.source.auth.authenticators.token import TokenAuthParams

def get_authenticator(self) -> AuthBase:
    return AuthBuilder.token(
        params=TokenAuthParams(token=self.config.authentication.params.token)
    )
```

#### SourceRecord Fields

```python
SourceRecord(
    id="unique_id",      # Required: unique identifier
    data={"key": "val"}, # Required: the actual record data
    destination_id=None  # Optional: for stream routing
)
```

### Incremental Sync (Optional)

Implement `get_records_after()` for incremental syncing:

```python
def get_records_after(self, source_state, pagination=None) -> SourceIteration:
    """Fetch only records after the last sync."""
    last_timestamp = source_state.last_run
    # Fetch records updated after last_timestamp
    ...
```

## Directory Structure

```
custom_sources/
├── README.md              # This file
├── jsonplaceholder/       # Tutorial example
│   └── source.py
└── my_custom_source/      # Your sources
    └── source.py
```

## Testing Your Source

### Quick Test (Python)

```bash
uv run python -c "
from bizon.source.discover import get_external_source_class_by_source_and_stream

# Load source
source_class = get_external_source_class_by_source_and_stream(
    source_name='my_source',
    stream_name='my_stream',
    filepath='custom_sources/my_source/source.py'
)
print(f'Streams: {source_class.streams()}')

# Instantiate
config_class = source_class.get_config_class()
config = config_class(name='my_source', stream='my_stream')
source = source_class(config=config)

# Test connection
success, error = source.check_connection()
print(f'Connection: {\"OK\" if success else error}')

# Fetch data
result = source.get()
print(f'Records: {len(result.records)}')
print(f'Sample: {result.records[0].data if result.records else None}')
"
```

### Full Pipeline Test

1. Start the platform: `make dev`
2. Create a pipeline via UI or API with your custom source
3. Check logs for any errors

## Tips

1. **Start simple** - Copy the jsonplaceholder example and modify
2. **Use self.session** - Pre-configured requests session with retry logic
3. **Test locally** - Use the logger destination for debugging
4. **Check connection** - Implement `check_connection()` properly for better error messages
