# Sana AI Source

Bizon source connector for the Sana AI Insight API. Fetches insight reports based on custom queries.

## Streams

| Stream | Description |
|--------|-------------|
| `insight_report` | Fetch insight report data based on a query |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `str` | Yes | Query to get data from the Sana Insight API |
| `domain` | `str` | Yes | Domain of your Sana instance (e.g., "yourcompany" for yourcompany.sana.ai) |

## Required Secrets

Add the following to your `.env` file:

```bash
SANA_CLIENT_ID=xxx          # OAuth 2.0 client ID
SANA_CLIENT_SECRET=xxx      # OAuth 2.0 client secret
SANA_REFRESH_TOKEN=xxx      # OAuth 2.0 refresh token
```

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/sana_ai/source.py",
    "name": "sana_ai",
    "stream": "insight_report",
    "authentication": {
      "type": "oauth",
      "params": {
        "client_id": "${SANA_CLIENT_ID}",
        "client_secret": "${SANA_CLIENT_SECRET}",
        "refresh_token": "${SANA_REFRESH_TOKEN}"
      }
    },
    "config": {
      "domain": "yourcompany",
      "query": "SELECT * FROM learning_completions WHERE date > '2024-01-01'"
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "sana_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py sana_ai insight_report

# With API connection
uv run python scripts/test_source.py sana_ai insight_report --fetch
```

## Notes

- Uses OAuth 2.0 authentication
- Creates async jobs for report generation and polls until completion
- Returns CSV data converted to records
