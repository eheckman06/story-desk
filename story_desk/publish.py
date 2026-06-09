"""Publish static site for GitHub Pages and cloud access."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"


def publish_site() -> Path:
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    latest_html = ROOT / "data" / "latest.html"
    latest_json = ROOT / "data" / "latest.json"

    if latest_html.exists():
        shutil.copy2(latest_html, SITE_DIR / "index.html")
        shutil.copy2(latest_html, SITE_DIR / "latest.html")
    if latest_json.exists():
        shutil.copy2(latest_json, SITE_DIR / "latest.json")

    db_html = ROOT / "data" / "database.html"
    db_json = ROOT / "data" / "database.json"
    if db_html.exists():
        shutil.copy2(db_html, SITE_DIR / "database.html")
    if db_json.exists():
        shutil.copy2(db_json, SITE_DIR / "database.json")

    meta = {}
    if latest_json.exists():
        meta = json.loads(latest_json.read_text())
    meta_path = SITE_DIR / "meta.json"
    meta_path.write_text(json.dumps({"date": meta.get("date"), "updated": meta.get("updated")}, indent=2))

    return SITE_DIR
