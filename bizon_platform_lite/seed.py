"""Database seeder for demo data.

Usage:
    uv run python -m bizon_platform_lite.seed

Or with reset (clears existing data first):
    uv run python -m bizon_platform_lite.seed --reset
"""

import asyncio
import sys

from sqlalchemy import delete, select

from bizon_platform_lite.db.models import Pipeline, PipelineRun, SavedConnector
from bizon_platform_lite.db.session import async_session

DEMO_PIPELINES = [
    {
        "name": "jsonplaceholder-posts-to-logger",
        "config": {
            "name": "jsonplaceholder-posts-to-logger",
            "source": {
                "source_file_path": "/custom_sources/jsonplaceholder/source.py",
                "name": "jsonplaceholder",
                "stream": "posts",
            },
            "destination": {
                "name": "logger",
                "config": {"dummy": "dummy"},
            },
        },
        "schedule": None,
        "enabled": True,
        "tags": ["demo", "custom-source"],
    },
    {
        "name": "jsonplaceholder-users-to-logger",
        "config": {
            "name": "jsonplaceholder-users-to-logger",
            "source": {
                "source_file_path": "/custom_sources/jsonplaceholder/source.py",
                "name": "jsonplaceholder",
                "stream": "users",
            },
            "destination": {
                "name": "logger",
                "config": {"dummy": "dummy"},
            },
        },
        "schedule": None,
        "enabled": False,
        "tags": ["demo", "custom-source"],
    },
]


async def seed_database(reset: bool = False) -> None:
    """Seed the database with demo data.

    Args:
        reset: If True, delete existing data before seeding.
    """
    async with async_session() as session:
        if reset:
            print("Resetting database...")
            await session.execute(delete(PipelineRun))
            await session.execute(delete(Pipeline))
            await session.execute(delete(SavedConnector))
            await session.commit()
            print("  Cleared all pipelines, runs, and saved connectors")

        # Check for existing demo pipelines
        existing_names = set()
        for pipeline_data in DEMO_PIPELINES:
            result = await session.execute(
                select(Pipeline).where(Pipeline.name == pipeline_data["name"])
            )
            if result.scalar_one_or_none():
                existing_names.add(pipeline_data["name"])

        # Create demo pipelines
        created_count = 0
        for pipeline_data in DEMO_PIPELINES:
            if pipeline_data["name"] in existing_names:
                print(f"  Skipping '{pipeline_data['name']}' (already exists)")
                continue

            pipeline = Pipeline(
                name=pipeline_data["name"],
                config=pipeline_data["config"],
                schedule=pipeline_data.get("schedule"),
                enabled=pipeline_data.get("enabled", True),
                tags=pipeline_data.get("tags"),
            )
            session.add(pipeline)
            created_count += 1
            print(f"  Created pipeline: {pipeline_data['name']}")

        await session.commit()

        if created_count > 0:
            print(f"\nSeeded {created_count} demo pipeline(s)")
        else:
            print("\nNo new pipelines created (all already exist)")


def main() -> None:
    """CLI entry point."""
    reset = "--reset" in sys.argv

    if reset:
        confirm = input("This will DELETE all existing data. Continue? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted")
            return

    print("Seeding database...")
    asyncio.run(seed_database(reset=reset))
    print("Done!")


if __name__ == "__main__":
    main()
