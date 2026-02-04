# Rootly Source

Bizon source connector for the Rootly API. Fetches incident management data including incidents, post-mortems, teams, and services.

## Streams

| Stream | Description |
|--------|-------------|
| `incidents` | All incidents with related data (statuses, causes, services, etc.) |
| `post_mortems` | Post-mortem reports with retrospective steps |
| `teams` | Team definitions |
| `services` | Service catalog |
| `users` | User accounts |
| `incident_action_items` | Action items from incidents |

## Configuration

No additional configuration fields required beyond authentication.

## Required Secrets

Add the following to your `.env` file:

```bash
ROOTLY_API_KEY=xxx  # Your Rootly API key
```

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/rootly/source.py",
    "name": "rootly",
    "stream": "incidents",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${ROOTLY_API_KEY}"
      }
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "rootly_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py rootly incidents

# With API connection
uv run python scripts/test_source.py rootly incidents --fetch
```

## Notes

- Incidents include related data: sub_statuses, causes, subscribers, services, groups, action_items, incident_post_mortem, feedbacks
- Post-mortems fetch and embed incident retrospective steps
- Uses page-based pagination
