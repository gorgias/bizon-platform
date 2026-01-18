"""CLI tool for testing custom sources locally."""

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="test-source",
    help="Test custom sources locally",
    add_completion=False,
)
console = Console()


def get_custom_sources_dir() -> Path:
    """Get the custom sources directory."""
    # Check environment variable first
    custom_dir = os.environ.get("CUSTOM_SOURCES_DIR", "./custom_sources")
    return Path(custom_dir)


def load_source_class(source_name: str) -> type:
    """Load and return the source class from a custom source."""
    from bizon.source.source import AbstractSource

    sources_dir = get_custom_sources_dir()
    source_file = sources_dir / source_name / "source.py"

    if not source_file.exists():
        rprint(f"[red]Error:[/red] Custom source '{source_name}' not found at {source_file}")
        raise typer.Exit(1)

    spec = importlib.util.spec_from_file_location(f"custom_source_{source_name}", source_file)
    if spec is None or spec.loader is None:
        rprint(f"[red]Error:[/red] Failed to load source module for '{source_name}'")
        raise typer.Exit(1)

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Find the source class
    source_class = None
    for name, obj in vars(module).items():
        if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
            source_class = obj
            break

    if source_class is None:
        rprint(f"[red]Error:[/red] No valid source class found in '{source_name}'")
        raise typer.Exit(1)

    return source_class


def load_config(
    source_name: str,
    config_json: Optional[str] = None,
    config_file: Optional[Path] = None,
) -> dict[str, Any]:
    """Load configuration from various sources."""
    config: dict[str, Any] = {}

    # 1. Try environment variables (SOURCE_NAME_KEY format)
    prefix = f"{source_name.upper()}_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix) :].lower()
            # Try to parse as JSON for complex values
            try:
                config[config_key] = json.loads(value)
            except json.JSONDecodeError:
                config[config_key] = value

    # 2. Load from config file (overrides env vars)
    if config_file:
        if not config_file.exists():
            # Try .secrets directory
            secrets_file = Path(".secrets") / f"{source_name}.json"
            if secrets_file.exists():
                config_file = secrets_file
            else:
                rprint(f"[red]Error:[/red] Config file not found: {config_file}")
                raise typer.Exit(1)

        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)

    # 3. Load from CLI JSON string (highest priority)
    if config_json:
        try:
            cli_config = json.loads(config_json)
            config.update(cli_config)
        except json.JSONDecodeError as e:
            rprint(f"[red]Error:[/red] Invalid JSON in --config: {e}")
            raise typer.Exit(1)

    return config


def list_available_sources() -> list[str]:
    """List all available custom sources."""
    sources_dir = get_custom_sources_dir()
    if not sources_dir.exists():
        return []

    sources = []
    for item in sources_dir.iterdir():
        if item.is_dir() and (item / "source.py").exists():
            sources.append(item.name)
    return sorted(sources)


@app.command()
def list() -> None:
    """List available custom sources."""
    sources = list_available_sources()

    if not sources:
        rprint("[yellow]No custom sources found.[/yellow]")
        rprint(f"Add sources to: {get_custom_sources_dir()}")
        return

    table = Table(title="Custom Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Streams", style="green")

    for source_name in sources:
        try:
            source_class = load_source_class(source_name)
            streams = ", ".join(source_class.streams())
        except Exception as e:
            streams = f"[red]Error: {e}[/red]"
        table.add_row(source_name, streams)

    console.print(table)


@app.command()
def check(
    source: str = typer.Argument(..., help="Source name"),
    stream: str = typer.Argument(..., help="Stream name"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config as JSON string"),
    config_file: Optional[Path] = typer.Option(None, "--config-file", "-f", help="Path to config JSON file"),
) -> None:
    """Test connection to a custom source."""
    rprint(f"\n[bold]Testing connection:[/bold] {source}/{stream}")

    source_class = load_source_class(source)
    config_class = source_class.get_config_class()

    # Check if stream is valid
    available_streams = source_class.streams()
    if stream not in available_streams:
        rprint(f"[red]Error:[/red] Stream '{stream}' not found.")
        rprint(f"Available streams: {', '.join(available_streams)}")
        raise typer.Exit(1)

    # Load config
    extra_config = load_config(source, config, config_file)

    try:
        # Create config with source file path for custom sources
        source_file_path = f"/custom_sources/{source}/source.py"
        source_config = config_class(
            name=source,
            stream=stream,
            source_file_path=source_file_path,
            **extra_config,
        )
        source_instance = source_class(config=source_config)

        # Test connection
        success, error_message = source_instance.check_connection()

        if success:
            rprint(Panel("[green]Connection successful![/green]", title="Result", border_style="green"))
        else:
            rprint(Panel(f"[red]Connection failed:[/red] {error_message}", title="Result", border_style="red"))
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        rprint(Panel(f"[red]Error:[/red] {e}", title="Result", border_style="red"))
        raise typer.Exit(1)


@app.command()
def fetch(
    source: str = typer.Argument(..., help="Source name"),
    stream: str = typer.Argument(..., help="Stream name"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of records to fetch"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config as JSON string"),
    config_file: Optional[Path] = typer.Option(None, "--config-file", "-f", help="Path to config JSON file"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
) -> None:
    """Fetch sample records from a custom source."""
    rprint(f"\n[bold]Fetching records:[/bold] {source}/{stream} (limit: {limit})")

    source_class = load_source_class(source)
    config_class = source_class.get_config_class()

    # Check if stream is valid
    available_streams = source_class.streams()
    if stream not in available_streams:
        rprint(f"[red]Error:[/red] Stream '{stream}' not found.")
        rprint(f"Available streams: {', '.join(available_streams)}")
        raise typer.Exit(1)

    # Load config
    extra_config = load_config(source, config, config_file)

    try:
        source_file_path = f"/custom_sources/{source}/source.py"
        source_config = config_class(
            name=source,
            stream=stream,
            source_file_path=source_file_path,
            **extra_config,
        )
        source_instance = source_class(config=source_config)

        # Fetch records
        result = source_instance.get()
        records = result.records[:limit]

        if raw:
            # Output raw JSON
            output = [{"id": r.id, "data": r.data} for r in records]
            print(json.dumps(output, indent=2, default=str))
        else:
            # Pretty print
            rprint(f"\n[bold green]Fetched {len(records)} record(s):[/bold green]\n")
            for i, record in enumerate(records, 1):
                rprint(f"[cyan]Record {i}[/cyan] (id: {record.id})")
                rprint(json.dumps(record.data, indent=2, default=str))
                rprint()

            if result.next_pagination:
                rprint(f"[dim]More records available (pagination: {result.next_pagination})[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        rprint(f"[red]Error fetching records:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def run(
    source: str = typer.Argument(..., help="Source name"),
    stream: str = typer.Argument(..., help="Stream name"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config as JSON string"),
    config_file: Optional[Path] = typer.Option(None, "--config-file", "-f", help="Path to config JSON file"),
) -> None:
    """Run a logger pipeline for the source (for debugging)."""
    from bizon.engine.engine import RunnerFactory

    rprint(f"\n[bold]Running logger pipeline:[/bold] {source}/{stream}")

    source_class = load_source_class(source)

    # Check if stream is valid
    available_streams = source_class.streams()
    if stream not in available_streams:
        rprint(f"[red]Error:[/red] Stream '{stream}' not found.")
        rprint(f"Available streams: {', '.join(available_streams)}")
        raise typer.Exit(1)

    # Load config
    extra_config = load_config(source, config, config_file)

    # Build pipeline config
    sources_dir = get_custom_sources_dir()
    source_file_path = str(sources_dir / source / "source.py")

    pipeline_config = {
        "name": f"test_{source}_{stream}",
        "source": {
            "name": source,
            "stream": stream,
            "source_file_path": source_file_path,
            **extra_config,
        },
        "destination": {
            "name": "logger",
            "config": {
                "dummy": "dummy",
            },
        },
    }

    rprint("\n[dim]Pipeline config:[/dim]")
    rprint(json.dumps(pipeline_config, indent=2))
    rprint()

    try:
        runner = RunnerFactory.create_from_config_dict(pipeline_config)
        runner.run()
        rprint(Panel("[green]Pipeline completed successfully![/green]", title="Result", border_style="green"))
    except Exception as e:
        rprint(Panel(f"[red]Pipeline failed:[/red] {e}", title="Result", border_style="red"))
        raise typer.Exit(1)


@app.command()
def streams(
    source: str = typer.Argument(..., help="Source name"),
) -> None:
    """List available streams for a source."""
    source_class = load_source_class(source)
    available_streams = source_class.streams()

    rprint(f"\n[bold]Streams for {source}:[/bold]")
    for stream in available_streams:
        rprint(f"  - {stream}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
