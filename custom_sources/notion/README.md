# Notion Source

Bizon source connector for the Notion API. Fetches databases, pages, blocks, and users from Notion workspaces.

## Streams

| Stream | Description |
|--------|-------------|
| `databases` | Fetch specific databases by ID |
| `data_sources` | Fetch data sources from databases |
| `pages` | Fetch pages from databases or by ID |
| `blocks` | Fetch blocks recursively from pages/databases |
| `blocks_markdown` | Fetch blocks and convert to markdown |
| `users` | Fetch all users accessible to the integration |
| `all_pages` | Fetch all pages accessible to the integration |
| `all_databases` | Fetch all databases accessible to the integration |
| `all_data_sources` | Fetch all data sources accessible to the integration |
| `all_blocks_markdown` | Fetch all blocks and convert to markdown |

## Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database_ids` | `List[str]` | For specific streams | List of Notion database IDs to fetch |
| `page_ids` | `List[str]` | For specific streams | List of Notion page IDs to fetch |
| `fetch_blocks_recursively` | `bool` | No | Whether to fetch nested blocks recursively (default: true) |
| `max_recursion_depth` | `int` | No | Maximum nesting depth (default: 5, max: 100) |
| `page_size` | `int` | No | Results per page (default: 100, max: 100) |
| `max_workers` | `int` | No | Concurrent workers for fetching (default: 3, max: 10) |
| `database_filters` | `Dict[str, Any]` | No | Map of database_id to Notion filter object |

## Required Secrets

Add the following to your `.env` file:

```bash
NOTION_API_KEY=secret_xxx  # Your Notion integration token
```

## Example Pipeline Config

```json
{
  "source": {
    "source_file_path": "/custom_sources/notion/source.py",
    "name": "notion",
    "stream": "all_blocks_markdown",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${NOTION_API_KEY}"
      }
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "your-project",
      "dataset": "notion_data"
    }
  }
}
```

### Fetching Specific Databases

```json
{
  "source": {
    "source_file_path": "/custom_sources/notion/source.py",
    "name": "notion",
    "stream": "pages",
    "authentication": {
      "type": "api_key",
      "params": {
        "token": "${NOTION_API_KEY}"
      }
    },
    "config": {
      "database_ids": ["abc123-def456", "ghi789-jkl012"],
      "database_filters": {
        "abc123-def456": {
          "property": "Status",
          "status": {"equals": "Published"}
        }
      }
    }
  }
}
```

## Testing

```bash
# Discovery only (no API key needed)
uv run python scripts/test_source.py notion users

# With API connection
uv run python scripts/test_source.py notion users --fetch
```

## Notes

- Uses Notion API version `2025-09-03`
- Implements exponential backoff with retry logic for rate limiting
- The `all_*` streams don't require `database_ids` or `page_ids` configuration
- Blocks are fetched with lineage tracking (parent_block_id, source_page_id, depth, etc.)
