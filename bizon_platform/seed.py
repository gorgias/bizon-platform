"""Database seeder for demo data.

Usage:
    uv run python -m bizon_platform.seed

Or with reset (clears existing data first):
    uv run python -m bizon_platform.seed --reset
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select

from bizon_platform.db.models import Pipeline, PipelineRun, SavedConnector
from bizon_platform.db.session import async_session

# Realistic demo pipelines that showcase the platform's capabilities
DEMO_PIPELINES = [
    {
        "name": "Stripe Payments → BigQuery",
        "config": {
            "name": "Stripe Payments → BigQuery",
            "source": {
                "name": "dummy",
                "stream": "payments",
            },
            "destination": {
                "name": "logger",
                "config": {"dummy": "dummy"},
            },
        },
        "schedule": "0 */6 * * *",  # Every 6 hours
        "enabled": True,
        "tags": ["production", "finance"],
    },
    {
        "name": "HubSpot Contacts → Snowflake",
        "config": {
            "name": "HubSpot Contacts → Snowflake",
            "source": {
                "name": "dummy",
                "stream": "contacts",
            },
            "destination": {
                "name": "logger",
                "config": {"dummy": "dummy"},
            },
        },
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "enabled": True,
        "tags": ["production", "crm"],
    },
    {
        "name": "GitHub Events → Data Lake",
        "config": {
            "name": "GitHub Events → Data Lake",
            "source": {
                "name": "dummy",
                "stream": "events",
            },
            "destination": {
                "name": "logger",
                "config": {"dummy": "dummy"},
            },
        },
        "schedule": "*/15 * * * *",  # Every 15 minutes
        "enabled": True,
        "tags": ["production", "engineering"],
    },
    {
        "name": "Pokemon API → Logger (Custom Source)",
        "config": {
            "name": "Pokemon API → Logger (Custom Source)",
            "source": {
                "source_file_path": "/custom_sources/pokeapi/source.py",
                "name": "pokeapi",
                "stream": "pokemon",
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
        "name": "JSONPlaceholder Posts → Logger",
        "config": {
            "name": "JSONPlaceholder Posts → Logger",
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
        "enabled": False,
        "tags": ["demo", "custom-source"],
    },
]

# Sample run logs for realistic demo experience
SAMPLE_LOGS_SUCCESS = """[2024-01-15 10:00:00] INFO: Starting pipeline execution
[2024-01-15 10:00:01] INFO: Connecting to source...
[2024-01-15 10:00:02] INFO: Source connection established
[2024-01-15 10:00:03] INFO: Fetching records from stream...
[2024-01-15 10:00:15] INFO: Retrieved 1,247 records
[2024-01-15 10:00:16] INFO: Applying transforms...
[2024-01-15 10:00:18] INFO: Writing to destination...
[2024-01-15 10:00:25] INFO: Successfully wrote 1,247 records
[2024-01-15 10:00:26] INFO: Pipeline completed successfully
"""

SAMPLE_LOGS_SUCCESS_SMALL = """[2024-01-15 08:00:00] INFO: Starting pipeline execution
[2024-01-15 08:00:01] INFO: Connecting to source...
[2024-01-15 08:00:02] INFO: Source connection established
[2024-01-15 08:00:03] INFO: Fetching records from stream...
[2024-01-15 08:00:05] INFO: Retrieved 42 records
[2024-01-15 08:00:06] INFO: Writing to destination...
[2024-01-15 08:00:07] INFO: Successfully wrote 42 records
[2024-01-15 08:00:08] INFO: Pipeline completed successfully
"""

SAMPLE_LOGS_FAILED = """[2024-01-14 14:00:00] INFO: Starting pipeline execution
[2024-01-14 14:00:01] INFO: Connecting to source...
[2024-01-14 14:00:02] ERROR: Connection failed: Rate limit exceeded
[2024-01-14 14:00:03] INFO: Retrying in 5 seconds... (attempt 1/3)
[2024-01-14 14:00:08] ERROR: Connection failed: Rate limit exceeded
[2024-01-14 14:00:09] INFO: Retrying in 10 seconds... (attempt 2/3)
[2024-01-14 14:00:19] ERROR: Connection failed: Rate limit exceeded
[2024-01-14 14:00:20] ERROR: Max retries exceeded. Pipeline failed.
"""


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
            result = await session.execute(select(Pipeline).where(Pipeline.name == pipeline_data["name"]))
            if result.scalar_one_or_none():
                existing_names.add(pipeline_data["name"])

        # Create demo pipelines
        created_pipelines = []
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
            created_pipelines.append(pipeline)
            print(f"  Created pipeline: {pipeline_data['name']}")

        await session.commit()

        # Refresh to get IDs
        for pipeline in created_pipelines:
            await session.refresh(pipeline)

        # Create sample runs for the first few pipelines
        if created_pipelines:
            await _create_sample_runs(session, created_pipelines)

        if created_pipelines:
            print(f"\nSeeded {len(created_pipelines)} demo pipeline(s)")
        else:
            print("\nNo new pipelines created (all already exist)")


async def _create_sample_runs(session, pipelines: list[Pipeline]) -> None:
    """Create sample pipeline runs for demo purposes."""
    now = datetime.utcnow()
    runs_created = 0

    for i, pipeline in enumerate(pipelines[:3]):  # Only first 3 pipelines get runs
        # Run 1: Successful run from 2 hours ago
        run1 = PipelineRun(
            id=uuid.uuid4(),
            pipeline_id=pipeline.id,
            status="success",
            triggered_by="schedule",
            started_at=now - timedelta(hours=2, minutes=30),
            finished_at=now - timedelta(hours=2, minutes=29),
            logs=SAMPLE_LOGS_SUCCESS if i == 0 else SAMPLE_LOGS_SUCCESS_SMALL,
            created_at=now - timedelta(hours=2, minutes=30),
        )
        session.add(run1)
        runs_created += 1

        # Run 2: Successful run from 8 hours ago
        run2 = PipelineRun(
            id=uuid.uuid4(),
            pipeline_id=pipeline.id,
            status="success",
            triggered_by="schedule",
            started_at=now - timedelta(hours=8, minutes=15),
            finished_at=now - timedelta(hours=8, minutes=14),
            logs=SAMPLE_LOGS_SUCCESS_SMALL,
            created_at=now - timedelta(hours=8, minutes=15),
        )
        session.add(run2)
        runs_created += 1

        # Run 3 (only for first pipeline): Failed run from yesterday
        if i == 0:
            run3 = PipelineRun(
                id=uuid.uuid4(),
                pipeline_id=pipeline.id,
                status="failed",
                triggered_by="schedule",
                started_at=now - timedelta(days=1, hours=2),
                finished_at=now - timedelta(days=1, hours=2) + timedelta(seconds=20),
                error="Rate limit exceeded after 3 retries",
                logs=SAMPLE_LOGS_FAILED,
                created_at=now - timedelta(days=1, hours=2),
            )
            session.add(run3)
            runs_created += 1

    await session.commit()
    print(f"  Created {runs_created} sample run(s)")


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
