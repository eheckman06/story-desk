#!/usr/bin/env python3
"""Run daily desk, update Canvas tab, and publish static site."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from story_desk.daily import run_daily

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily story desk outputs.")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    result = run_daily(args.date)
    if not os.environ.get("CI"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "update_canvas.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "update_database_canvas.py")], check=True)

    print(f"Fetched {result['fetched']} headlines")
    print(f"Built {result['pitches']} pitches ({result['timely']} timely + {result['evergreen']} evergreen)")
    print(f"Canvas tab: ~/.cursor/projects/Users-elizabeth-heckman-Projects-story-desk/canvases/story-desk.canvas.tsx")
    print(f"Database canvas: ~/.cursor/projects/Users-elizabeth-heckman-Projects-story-desk/canvases/story-desk-database.canvas.tsx")
    print(f"Browser (local): {result['html_path']}")
    print(f"Database (local): {result.get('database_html', 'data/database.html')}")
    print(f"Cloud site folder: {result['site_dir']}/index.html")


if __name__ == "__main__":
    main()
