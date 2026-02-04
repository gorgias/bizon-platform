# Noticeable Source

Bizon source connector for the Noticeable GraphQL API. Fetches publications, email events, and subscriptions.

## Streams

| Stream | Description |
|--------|-------------|
| `email_opened_events` | Email open tracking events |
| `publications` | Published changelog entries |
| `publication_comments` | Comments on publications |
| `email_subscriptions` | Email subscriber list |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | `str` | Yes | Noticeable project ID |

## Required Secrets

Add the following to your `.env` file:

```bash
NOTICEABLE_API_KEY=xxx  # Your Noticeable API key
```

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/noticeable/source.py",
    "name": "noticeable",
    "stream": "publications",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${NOTICEABLE_API_KEY}"
      }
    },
    "config": {
      "project_id": "your-project-id"
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "noticeable_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py noticeable publications

# With API connection
uv run python scripts/test_source.py noticeable publications --fetch
```

## Notes

- Uses GraphQL API at `https://api.noticeable.io/graphql`
- Supports cursor-based pagination
- API key authentication via Bearer token
