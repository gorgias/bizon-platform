"""Bizon pipeline runner for subprocess execution.

This script is executed by SubprocessBackend and reads config from stdin.
All logs go to stderr (captured by parent process).
"""

import json
import os
import sys


def main():
    # Read config from stdin
    config_json = sys.stdin.read()
    config = json.loads(config_json)

    # Change to output directory if specified
    output_dir = os.environ.get("BIZON_OUTPUT_DIR")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)

    # Import bizon here to avoid loading at module level
    from bizon.engine.engine import RunnerFactory

    try:
        # Run the pipeline (logs go to stderr via loguru)
        runner = RunnerFactory.create_from_config_dict(config)
        result = runner.run()

        # Check RunnerStatus.is_success to detect failures
        if not result.is_success:
            print(result.to_string(), file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
