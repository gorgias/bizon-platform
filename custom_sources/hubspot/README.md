# HubSpot Source

Bizon source connector for the HubSpot CRM API. Fetches contacts, companies, deals, and custom objects.

## Streams

| Stream | Description |
|--------|-------------|
| `contacts` | Contact records |
| `companies` | Company records |
| `deals` | Deal records |
| `2-48391801` | Custom object: Partner Onboarding |
| `2-48061043` | Custom object: ARR Forecasts |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `properties.strategy` | `str` | No | `"all"` or `"selected"` (default: all) |
| `properties.selected_properties` | `List[str]` | No | List of property names to fetch if strategy is "selected" |
| `associations_types` | `List[str]` | No | List of association types to retrieve |

## Required Secrets

### OAuth 2.0 (Recommended)

```bash
HUBSPOT_CLIENT_ID=xxx
HUBSPOT_CLIENT_SECRET=xxx
HUBSPOT_REFRESH_TOKEN=xxx
```

### API Key

```bash
HUBSPOT_API_KEY=xxx
```

## Example Pipeline Config

### Using OAuth 2.0

```json
{
  "source": {
    "source_file_path": "/custom_sources/hubspot/source.py",
    "name": "hubspot",
    "stream": "contacts",
    "authentication": {
      "type": "oauth",
      "params": {
        "client_id": "${HUBSPOT_CLIENT_ID}",
        "client_secret": "${HUBSPOT_CLIENT_SECRET}",
        "refresh_token": "${HUBSPOT_REFRESH_TOKEN}"
      }
    },
    "config": {
      "properties": {
        "strategy": "selected",
        "selected_properties": ["email", "firstname", "lastname", "company"]
      },
      "associations_types": ["companies", "deals"]
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "hubspot_data"
    }
  }
}
```

### Using API Key

```json
{
  "source": {
    "source_file_path": "/custom_sources/hubspot/source.py",
    "name": "hubspot",
    "stream": "deals",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${HUBSPOT_API_KEY}"
      }
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "hubspot_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py hubspot contacts

# With API connection
uv run python scripts/test_source.py hubspot contacts --fetch
```

## Notes

- Uses HubSpot CRM v3 API
- Supports both OAuth 2.0 and API key authentication
- Implements aggressive retry policy for rate limiting (up to 50 retries)
- Custom objects use their numeric IDs as stream names
