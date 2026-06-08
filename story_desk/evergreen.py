"""Rotate evergreen culture/media pitches."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_evergreen_pool() -> list[dict]:
    data = json.loads((ROOT / "config" / "evergreen.json").read_text())
    return data["pitches"]


def pick_evergreen_pitches(run_date: date | None = None, count: int = 3) -> list[dict]:
    run_date = run_date or date.today()
    pool = load_evergreen_pool()
    if not pool or count <= 0:
        return []

    start = run_date.timetuple().tm_yday % len(pool)
    picks: list[dict] = []
    for offset in range(len(pool)):
        if len(picks) >= count:
            break
        pitch = dict(pool[(start + offset) % len(pool)])
        pitch["evergreen"] = True
        pitch["source_kind"] = "evergreen"
        picks.append(pitch)

    return picks
