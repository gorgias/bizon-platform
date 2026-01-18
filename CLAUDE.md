# Bizon Platform Lite - Claude Instructions

## Project Overview

Bizon Platform Lite is a lightweight, single-tenant data pipeline orchestration platform. It runs bizon data pipelines with scheduling, worker execution, and a React UI.

## Architecture

- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL
- **Worker**: Subprocess-based pipeline execution with APScheduler
- **UI**: React + Vite + TailwindCSS
- **Package**: `bizon_platform_lite/`

## Key Commands

```bash
make dev          # Start dev environment with hot reload
make prod         # Start production environment
make test         # Run tests
make lint         # Run linter
```

## Custom Sources

Custom sources are the primary way users extend bizon. They live in `custom_sources/`.

### Creating a Custom Source

When asked to create a custom source:

1. Create a directory: `custom_sources/{source_name}/`
2. Create `source.py` with:
   - A config class extending `SourceConfig`
   - A source class extending `AbstractSource`
   - Required methods: `streams()`, `get_config_class()`, `get_authenticator()`, `check_connection()`, `get_total_records_count()`, `get()`

### Source Template

```python
from typing import List, Tuple
from requests.auth import AuthBase
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource

class MySourceConfig(SourceConfig):
    # Add custom config fields
    pass

class MySource(AbstractSource):
    def __init__(self, config: MySourceConfig):
        super().__init__(config)
        self.config: MySourceConfig = config

    @staticmethod
    def streams() -> List[str]:
        return ["stream1", "stream2"]

    @staticmethod
    def get_config_class() -> type:
        return MySourceConfig

    def get_authenticator(self) -> AuthBase | None:
        return None

    def check_connection(self) -> Tuple[bool, str | None]:
        return True, None

    def get_total_records_count(self) -> int | None:
        return None

    def get(self, pagination: dict = None) -> SourceIteration:
        # Fetch logic here
        return SourceIteration(
            next_pagination={},
            records=[SourceRecord(id="1", data={"key": "value"})]
        )
```

### Pipeline Config with Custom Source

```json
{
  "source": {
    "source_file_path": "/custom_sources/my_source/source.py",
    "name": "my_source",
    "stream": "stream1"
  },
  "destination": {
    "name": "bigquery",
    "config": {"project_id": "...", "dataset": "..."}
  }
}
```

## File Locations

- Backend code: `bizon_platform_lite/`
- API routes: `bizon_platform_lite/api/routes/`
- Database models: `bizon_platform_lite/db/models.py`
- Worker: `bizon_platform_lite/worker/`
- Scheduler: `bizon_platform_lite/scheduler/`
- Frontend: `ui/`
- Custom sources: `custom_sources/`
- Tests: `tests/`

## Available Destinations

- `logger` - Debug logging
- `bigquery` - Google BigQuery
- `bigquery_streaming` - BigQuery streaming insert
- `file` - Local file output

## Available Built-in Sources

Run `bizon source list` or check the API at `/api/connectors/sources` to see all available sources.

## Testing

```bash
uv run pytest -v                    # All tests
uv run pytest tests/unit/ -v        # Unit tests only
uv run pytest tests/api/ -v         # API tests only
```

### Testing Custom Sources

Always test a custom source after creating it:

```bash
uv run python -c "
from bizon.source.discover import get_external_source_class_by_source_and_stream

source_class = get_external_source_class_by_source_and_stream(
    source_name='SOURCE_NAME',
    stream_name='STREAM_NAME',
    filepath='custom_sources/SOURCE_NAME/source.py'
)
print(f'Streams: {source_class.streams()}')

config = source_class.get_config_class()(name='SOURCE_NAME', stream='STREAM_NAME')
source = source_class(config=config)

success, error = source.check_connection()
print(f'Connection: {\"OK\" if success else error}')

result = source.get()
print(f'Records: {len(result.records)}')
if result.records:
    print(f'Sample: {result.records[0].data}')
"
```
