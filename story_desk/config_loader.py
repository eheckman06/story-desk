"""Load theme and source configuration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text())


def load_themes() -> dict:
    return load_json("themes.json")


def load_sources() -> dict:
    return load_json("sources.json")
