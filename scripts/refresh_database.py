#!/usr/bin/env python3
"""Refresh database export and interactive views without re-fetching RSS."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from story_desk.database_view import write_database_html


def main() -> None:
    path = write_database_html()
    print(f"Exported: {path}")
    print(f"JSON: {path.parent / 'database.json'}")

    if not os.environ.get("CI"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "update_database_canvas.py")], check=True)


if __name__ == "__main__":
    main()
