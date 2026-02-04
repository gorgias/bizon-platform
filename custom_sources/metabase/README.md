# Metabase Source

Bizon source connector for the Metabase API. Fetches users, cards (questions), dashboards, and permission groups.

## Streams

| Stream | Description |
|--------|-------------|
| `users` | User accounts (paginated) |
| `cards` | Saved questions/cards |
| `dashboards` | Dashboard definitions |
| `permissions_groups` | Permission group definitions |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base_url` | `str` | Yes | Base URL of your Metabase instance (e.g., `https://metabase.example.com`) |
| `page_size` | `int` | No | Records per page for users endpoint (default: 50, max: 100) |

## Required Secrets

Add the following to your `.env` file:

```bash
METABASE_API_KEY=xxx  # Your Metabase API key
```

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/metabase/source.py",
    "name": "metabase",
    "stream": "cards",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${METABASE_API_KEY}"
      }
    },
    "config": {
      "base_url": "https://metabase.yourcompany.com"
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "metabase_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py metabase cards

# With API connection
uv run python scripts/test_source.py metabase cards --fetch
```

## Notes

- Uses custom `x-api-key` header (not Bearer token)
- Only `users` stream is paginated; others return all records
- Implements retry logic with exponential backoff
