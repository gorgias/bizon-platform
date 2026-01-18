# CLI Tool

**Priority:** P2
**Effort:** Medium
**Status:** Planned

## Overview

Command-line interface for local development, scripting, and CI/CD integration. Enables developers to manage pipelines without the UI.

## Why This Matters

- **Developer workflow** - Code editors, not browsers
- **Automation** - Script pipeline management
- **CI/CD** - Integrate with deployment pipelines
- **Offline development** - Work locally before deploying

## Commands

### Project Management

```bash
# Initialize a new Bizon project
bizon init
# Creates:
# - bizon.yaml (project config)
# - custom_sources/ (directory)
# - pipelines/ (directory for YAML definitions)

# Validate project structure
bizon validate
```

### Custom Source Development

```bash
# Create a new custom source from template
bizon source create my_api
# Creates custom_sources/my_api/source.py with boilerplate

# Test custom source locally
bizon source test my_api --stream users
# Runs check_connection() and fetches sample records

# List discovered custom sources
bizon source list
```

### Pipeline Management

```bash
# Create pipeline from YAML file
bizon pipeline create pipelines/stripe-to-bigquery.yaml

# List pipelines
bizon pipeline list
bizon pipeline list --status enabled
bizon pipeline list --format json

# Get pipeline details
bizon pipeline get stripe-to-bigquery
bizon pipeline get stripe-to-bigquery --format yaml

# Update pipeline from file
bizon pipeline update stripe-to-bigquery pipelines/stripe-to-bigquery.yaml

# Delete pipeline
bizon pipeline delete stripe-to-bigquery

# Enable/disable
bizon pipeline enable stripe-to-bigquery
bizon pipeline disable stripe-to-bigquery
```

### Pipeline Execution

```bash
# Run pipeline
bizon run stripe-to-bigquery
bizon run stripe-to-bigquery --wait  # Wait for completion
bizon run stripe-to-bigquery --tail  # Stream logs

# Check run status
bizon run status <run_id>

# Get run logs
bizon run logs <run_id>
bizon run logs <run_id> --follow

# Cancel running pipeline
bizon run cancel <run_id>

# List recent runs
bizon runs --pipeline stripe-to-bigquery --limit 10
```

### Configuration

```bash
# Set server URL
bizon config set server https://bizon.example.com

# Set authentication
bizon config set auth.password <password>

# View config
bizon config show

# Test connection
bizon config test
```

### Deployment

```bash
# Push local pipelines to server
bizon deploy
bizon deploy --dry-run  # Preview changes

# Pull pipelines from server to local
bizon pull
bizon pull --pipeline stripe-to-bigquery
```

## Project Structure

```
my-project/
├── bizon.yaml              # Project configuration
├── custom_sources/
│   ├── my_api/
│   │   └── source.py
│   └── another_source/
│       └── source.py
└── pipelines/
    ├── stripe-to-bigquery.yaml
    ├── hubspot-to-snowflake.yaml
    └── daily-reports.yaml
```

### bizon.yaml

```yaml
# Project configuration
version: "1"
name: my-data-project

# Server connection (can be overridden by env vars)
server:
  url: https://bizon.example.com
  # Password from BIZON_PASSWORD env var

# Custom source settings
custom_sources:
  directory: ./custom_sources

# Pipeline settings
pipelines:
  directory: ./pipelines
  # Default values for all pipelines
  defaults:
    enabled: false
    schedule: null
```

## Implementation

### Package Structure

```
bizon-cli/
├── bizon_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # Main CLI entry point
│   ├── config.py           # Configuration management
│   ├── api.py              # API client
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── init.py
│   │   ├── source.py
│   │   ├── pipeline.py
│   │   ├── run.py
│   │   └── deploy.py
│   └── templates/
│       ├── bizon.yaml
│       └── source.py.jinja
├── pyproject.toml
└── README.md
```

### CLI Entry Point

```python
# bizon_cli/cli.py
import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option()
def cli():
    """Bizon CLI - Pipeline orchestration from the command line."""
    pass


@cli.command()
@click.option("--name", prompt="Project name", default="my-bizon-project")
def init(name: str):
    """Initialize a new Bizon project."""
    from bizon_cli.commands.init import init_project
    init_project(name)


@cli.group()
def source():
    """Manage custom sources."""
    pass


@source.command("create")
@click.argument("name")
def source_create(name: str):
    """Create a new custom source."""
    from bizon_cli.commands.source import create_source
    create_source(name)


@source.command("test")
@click.argument("name")
@click.option("--stream", required=True)
def source_test(name: str, stream: str):
    """Test a custom source."""
    from bizon_cli.commands.source import test_source
    test_source(name, stream)


@cli.group()
def pipeline():
    """Manage pipelines."""
    pass


@pipeline.command("list")
@click.option("--status", type=click.Choice(["enabled", "disabled"]))
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table")
def pipeline_list(status: str, format: str):
    """List pipelines."""
    from bizon_cli.commands.pipeline import list_pipelines
    list_pipelines(status, format)


@pipeline.command("create")
@click.argument("file", type=click.Path(exists=True))
def pipeline_create(file: str):
    """Create pipeline from YAML file."""
    from bizon_cli.commands.pipeline import create_pipeline
    create_pipeline(file)


# ... more commands ...


if __name__ == "__main__":
    cli()
```

### API Client

```python
# bizon_cli/api.py
import httpx
from bizon_cli.config import get_config

class BizonClient:
    def __init__(self):
        config = get_config()
        self.base_url = config.server_url
        self.auth = None
        if config.password:
            self.auth = httpx.BasicAuth("admin", config.password)

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}/api{path}"
        with httpx.Client(auth=self.auth) as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    def list_pipelines(self, status: str | None = None):
        params = {}
        if status:
            params["enabled"] = status == "enabled"
        return self._request("GET", "/pipelines", params=params)

    def create_pipeline(self, data: dict):
        return self._request("POST", "/pipelines", json=data)

    def trigger_run(self, pipeline_id: str):
        return self._request("POST", f"/pipelines/{pipeline_id}/run")

    def get_run(self, run_id: str):
        return self._request("GET", f"/pipelines/runs/{run_id}")

    def get_run_logs(self, run_id: str):
        return self._request("GET", f"/pipelines/runs/{run_id}/logs")

    # ... more methods ...
```

### Rich Output

```python
# bizon_cli/commands/pipeline.py
from rich.table import Table
from rich.console import Console
from bizon_cli.api import BizonClient

console = Console()

def list_pipelines(status: str | None, format: str):
    client = BizonClient()
    pipelines = client.list_pipelines(status)

    if format == "json":
        import json
        console.print(json.dumps(pipelines, indent=2))
    elif format == "yaml":
        import yaml
        console.print(yaml.dump(pipelines))
    else:
        table = Table(title="Pipelines")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Schedule")
        table.add_column("Last Run")

        for p in pipelines:
            status = "Enabled" if p["enabled"] else "Disabled"
            table.add_row(
                p["name"],
                status,
                p.get("schedule") or "-",
                p.get("last_run_at") or "Never"
            )

        console.print(table)
```

### Source Testing

```python
# bizon_cli/commands/source.py
import importlib.util
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def test_source(name: str, stream: str):
    """Test a custom source locally."""
    source_path = Path(f"custom_sources/{name}/source.py")

    if not source_path.exists():
        console.print(f"[red]Source not found: {source_path}[/red]")
        return

    # Dynamic import
    spec = importlib.util.spec_from_file_location(f"source_{name}", source_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find AbstractSource subclass
    from bizon.source.source import AbstractSource
    source_class = None
    for obj in vars(module).values():
        if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
            source_class = obj
            break

    if not source_class:
        console.print("[red]No AbstractSource subclass found[/red]")
        return

    console.print(f"[cyan]Testing {name}:{stream}[/cyan]")

    # Check streams
    streams = source_class.streams()
    if stream not in streams:
        console.print(f"[red]Stream '{stream}' not found. Available: {streams}[/red]")
        return

    # Create instance
    config_class = source_class.get_config_class()
    config = config_class(name=name, stream=stream)
    source = source_class(config=config)

    # Test connection
    console.print("Testing connection...")
    success, error = source.check_connection()
    if success:
        console.print("[green]Connection OK[/green]")
    else:
        console.print(f"[red]Connection failed: {error}[/red]")
        return

    # Fetch sample records
    console.print("Fetching sample records...")
    result = source.get()

    console.print(f"[green]Fetched {len(result.records)} records[/green]")

    if result.records:
        # Show sample record
        table = Table(title="Sample Record")
        record = result.records[0]
        for key, value in record.data.items():
            table.add_row(key, str(value)[:50])
        console.print(table)
```

## Installation

```bash
# From PyPI
pip install bizon-cli

# Or with uv
uv tool install bizon-cli

# Verify
bizon --version
```

## Configuration File

```yaml
# ~/.config/bizon/config.yaml
servers:
  default:
    url: https://bizon.example.com
    password: ${BIZON_PASSWORD}  # From env var

  staging:
    url: https://staging.bizon.example.com

current_server: default
```

## Shell Completion

```bash
# Bash
bizon --install-completion bash

# Zsh
bizon --install-completion zsh

# Fish
bizon --install-completion fish
```

## Future Enhancements

- **Watch mode** - Auto-deploy on file changes
- **Diff view** - Show changes before deploy
- **Rollback** - Revert to previous version
- **Secrets management** - Secure credential handling
- **Plugins** - Extensible command system
