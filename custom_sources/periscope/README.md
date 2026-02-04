# Periscope Source

Bizon source connector for Periscope Data (Sisense). Fetches charts, dashboards, views, and users using cookie-based authentication.

## Streams

| Stream | Description |
|--------|-------------|
| `charts` | Charts/widgets from dashboards (filtered by database_id) |
| `dashboards` | Dashboard definitions |
| `dashboards_metadata` | Dashboard metadata from search API |
| `databases` | Connected database configurations |
| `users` | User accounts |
| `views` | SQL views |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workspace_name` | `str` | Yes | Name of the Periscope workspace |
| `client_site_id` | `int` | Yes | Client site ID |
| `database_id` | `int` | Yes | Filter charts by this database ID |
| `x_csrf_token` | `str` | Yes | CSRF token for requests |

## Required Secrets

Add the following to your `.env` file:

```bash
PERISCOPE_CF_BM=xxx              # Cloudflare __cf_bm cookie
PERISCOPE_SESSION=xxx            # periscope_session cookie
PERISCOPE_CSRF_TOKEN=xxx         # X-CSRF-Token header value
```

## Getting Credentials

1. Log into Periscope Data in your browser
2. Open Developer Tools (F12) > Network tab
3. Navigate to any page and find a request to `app.periscopedata.com`
4. From the request headers, copy:
   - `Cookie: __cf_bm=xxx` -> `PERISCOPE_CF_BM`
   - `Cookie: periscope_session=xxx` -> `PERISCOPE_SESSION`
   - `X-CSRF-Token: xxx` -> `PERISCOPE_CSRF_TOKEN`
5. From the URL parameters, note your `client_site_id`

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/periscope/source.py",
    "name": "periscope",
    "stream": "charts",
    "authentication": {
      "type": "cookies",
      "params": {
        "cookies": {
          "cf_bm": "${PERISCOPE_CF_BM}",
          "periscope_session": "${PERISCOPE_SESSION}"
        }
      }
    },
    "config": {
      "workspace_name": "your-workspace",
      "client_site_id": 12345,
      "database_id": 67890,
      "x_csrf_token": "${PERISCOPE_CSRF_TOKEN}"
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "periscope_data"
    }
  }
}
```

## Testing

```bash
# Discovery only
uv run python scripts/test_source.py periscope charts

# With API connection
uv run python scripts/test_source.py periscope charts --fetch
```

## Notes

- Uses cookie-based authentication (requires browser session cookies)
- Cookies expire periodically and need to be refreshed
- Charts are fetched in parallel batches of 10 dashboards
- Charts are filtered by `database_id` configuration
- Extracts raw text from textbox charts
