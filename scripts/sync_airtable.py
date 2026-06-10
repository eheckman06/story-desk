#!/usr/bin/env python3
"""Sync and inspect Fox article performance from Airtable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from story_desk.airtable_sync import (  # noqa: E402
    airtable_config,
    analyze_performance,
    list_tables,
    sync_airtable,
)


def cmd_list_tables() -> None:
    cfg = airtable_config()
    tables = list_tables(cfg["token"], cfg["base_id"])
    if not tables:
        print("No tables found in this base.")
        return

    print(f"Base: {cfg['base_id']}\n")
    for table in tables:
        print(f"- {table['name']}")
        print(f"  id: {table['id']}")
        views = table.get("views") or []
        if views:
            view_names = ", ".join(view["name"] for view in views[:8])
            print(f"  views: {view_names}")
        fields = table.get("fields") or []
        if fields:
            field_names = ", ".join(field["name"] for field in fields[:12])
            suffix = " ..." if len(fields) > 12 else ""
            print(f"  fields: {field_names}{suffix}")
        print()

    print("Add the table name to data/.env:")
    print("  AIRTABLE_TABLE_NAME=<table name from above>")
    print("Optional:")
    print("  AIRTABLE_VIEW_NAME=<view name>")


def cmd_sync() -> None:
    result = sync_airtable()
    print(json.dumps(result, indent=2))


def cmd_analyze() -> None:
    result = analyze_performance()
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Fox performance data from Airtable.")
    parser.add_argument("--list-tables", action="store_true", help="List tables/views/fields in the base")
    parser.add_argument("--sync", action="store_true", help="Pull records into data/airtable/latest.json and SQLite")
    parser.add_argument("--analyze", action="store_true", help="Show top-performing synced articles")
    args = parser.parse_args()

    if args.list_tables:
        cmd_list_tables()
    elif args.sync:
        cmd_sync()
    elif args.analyze:
        cmd_analyze()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
