#!/usr/bin/env python
"""Test SpotDraft pipeline by fetching contracts and saving to JSONL file."""

import json
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from bizon.source.discover import get_external_source_class_by_source_and_stream

# Config
OUTPUT_FILE = "output/spotdraft_contracts.jsonl"
MAX_RECORDS = 5  # Limit for testing


def main():
    print("Loading SpotDraft source...")
    source_class = get_external_source_class_by_source_and_stream(
        source_name="spotdraft",
        stream_name="contracts",
        filepath="custom_sources/spotdraft/source.py",
    )

    # Get credentials from environment
    client_id = os.environ.get("SPOTDRAFT_CLIENT_ID")
    client_secret = os.environ.get("SPOTDRAFT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: SPOTDRAFT_CLIENT_ID and SPOTDRAFT_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    print("Creating source config...")
    config = source_class.get_config_class()(
        name="spotdraft",
        stream="contracts",
        client_id=client_id,
        client_secret=client_secret,
        extract_pdf_text=True,
    )

    source = source_class(config=config)

    # Test connection
    print("Testing connection...")
    success, error = source.check_connection()
    if not success:
        print(f"ERROR: Connection failed: {error}")
        sys.exit(1)
    print("Connection OK!")

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Fetch records
    print(f"\nFetching up to {MAX_RECORDS} contracts...")
    source.PAGE_SIZE = MAX_RECORDS  # Limit page size for testing

    result = source.get()

    print(f"Fetched {len(result.records)} records")
    print(f"Has more pages: {bool(result.next_pagination)}")

    # Write to JSONL file
    print(f"\nWriting to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        for record in result.records:
            f.write(json.dumps(record.data, default=str) + "\n")

    print(f"Done! Wrote {len(result.records)} records to {OUTPUT_FILE}")

    # Print sample
    if result.records:
        print("\n--- Sample Record ---")
        sample = result.records[0].data
        print(f"ID: {sample['id']}")
        print(f"Title: {sample.get('title')}")
        print(f"Status: {sample.get('status')}")
        print(f"Created: {sample.get('created_at')}")
        print(f"Has key_pointers: {sample.get('key_pointers') is not None}")
        print(f"Has download_url: {sample.get('download_url') is not None}")
        pdf_text = sample.get("pdf_text")
        if pdf_text:
            print(f"PDF text length: {len(pdf_text)} chars")
            print(f"PDF text preview: {pdf_text[:200]}...")
        else:
            print("PDF text: None")


if __name__ == "__main__":
    main()
