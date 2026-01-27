#!/usr/bin/env python
"""Test a custom source with automatic .env loading.

Usage:
    uv run python scripts/test_source.py <source_name> <stream_name> [--fetch]

Examples:
    # Test discovery only
    uv run python scripts/test_source.py buildbetter signals

    # Test with actual API call (requires API key in .env)
    uv run python scripts/test_source.py buildbetter signals --fetch
"""

import argparse
import sys
from pathlib import Path

from bizon.source.discover import get_external_source_class_by_source_and_stream
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()


def test_source(source_name: str, stream_name: str, fetch: bool = False) -> bool:
    """Test a custom source."""
    filepath = f"custom_sources/{source_name}/source.py"

    if not Path(filepath).exists():
        print(f"Error: Source file not found: {filepath}")
        return False

    print(f"Testing source: {source_name}/{stream_name}")
    print(f"File: {filepath}")
    print()

    # Discovery test
    try:
        source_class = get_external_source_class_by_source_and_stream(
            source_name=source_name,
            stream_name=stream_name,
            filepath=filepath,
        )
        print(f"Streams: {source_class.streams()}")

        config_class = source_class.get_config_class()
        config_fields = list(config_class.model_fields.keys())
        print(f"Config fields: {config_fields}")
        print()
    except Exception as e:
        print(f"Discovery failed: {e}")
        return False

    if not fetch:
        print("Discovery test passed. Use --fetch to test API connection.")
        return True

    # Build config from environment variables
    import os

    config_kwargs = {
        "name": source_name,
        "stream": stream_name,
    }

    # Find secret fields (fields that aren't in base SourceConfig)
    base_fields = {"name", "stream", "source_file_path", "sync_mode", "cursor_field",
                   "force_ignore_checkpoint", "authentication", "max_iterations",
                   "api_config", "init_pipeline"}

    secret_fields = [f for f in config_fields if f not in base_fields]

    for field in secret_fields:
        env_var = f"{source_name.upper()}_{field.upper()}"
        value = os.environ.get(env_var)
        if value:
            config_kwargs[field] = value
            print(f"Loaded {field} from ${env_var}")
        else:
            print(f"Warning: {env_var} not set in environment")

    print()

    # Connection test
    try:
        config = config_class(**config_kwargs)
        source = source_class(config=config)

        print("Testing connection...")
        success, error = source.check_connection()
        if success:
            print("Connection: OK")
        else:
            print(f"Connection failed: {error}")
            return False
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

    # Fetch test
    try:
        print("Fetching records...")
        result = source.get()
        print(f"Records fetched: {len(result.records)}")
        if result.records:
            print(f"Sample record ID: {result.records[0].id}")
            # Print first few keys of data
            data = result.records[0].data
            keys = list(data.keys())[:5]
            print(f"Sample data keys: {keys}")
        if result.next_pagination:
            print("Has more pages: Yes")
        else:
            print("Has more pages: No")
    except Exception as e:
        print(f"Fetch test failed: {e}")
        return False

    print()
    print("All tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test a custom source")
    parser.add_argument("source_name", help="Name of the source (e.g., buildbetter)")
    parser.add_argument("stream_name", help="Name of the stream (e.g., signals)")
    parser.add_argument("--fetch", action="store_true", help="Test actual API connection")

    args = parser.parse_args()

    success = test_source(args.source_name, args.stream_name, args.fetch)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
