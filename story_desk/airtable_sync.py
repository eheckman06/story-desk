"""Pull Fox article performance data from Airtable."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from story_desk.config_loader import load_json
from story_desk.db import connect, init_db
from story_desk.env import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "data" / "airtable"
META_API = "https://api.airtable.com/v0/meta/bases/{base_id}/tables"
RECORDS_API = "https://api.airtable.com/v0/{base_id}/{table_ref}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def airtable_config() -> dict[str, str]:
    load_dotenv()
    token = os.environ.get("AIRTABLE_TOKEN", "").strip()
    base_id = os.environ.get("AIRTABLE_BASE_ID", "").strip()
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "").strip()
    view_name = os.environ.get("AIRTABLE_VIEW_NAME", "").strip()
    if not token:
        raise SystemExit(
            "Missing AIRTABLE_TOKEN. Add it to data/.env — see data/.env.example"
        )
    if not base_id:
        raise SystemExit(
            "Missing AIRTABLE_BASE_ID. Use appbfEwPkkvJmE7l7 for your base."
        )
    return {
        "token": token,
        "base_id": base_id,
        "table_name": table_name,
        "view_name": view_name,
    }


def _request(url: str, token: str) -> dict | list:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Airtable API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Airtable request failed: {exc.reason}") from exc


def list_tables(token: str, base_id: str) -> list[dict]:
    payload = _request(META_API.format(base_id=base_id), token)
    return payload.get("tables", [])


def fetch_records(
    token: str,
    base_id: str,
    table_ref: str,
    view_name: str = "",
) -> list[dict]:
    records: list[dict] = []
    params: dict[str, str] = {"pageSize": "100"}
    if view_name:
        params["view"] = view_name

    offset = ""
    while True:
        query = dict(params)
        if offset:
            query["offset"] = offset
        url = f"{RECORDS_API.format(base_id=base_id, table_ref=urllib.parse.quote(table_ref))}?{urllib.parse.urlencode(query)}"
        payload = _request(url, token)
        records.extend(payload.get("records", []))
        offset = payload.get("offset", "")
        if not offset:
            break
    return records


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def map_fields(fields: dict[str, Any]) -> dict[str, Any]:
    mapping = load_json("airtable.json")["field_map"]
    normalized = {_normalize_key(key): (key, value) for key, value in fields.items()}
    mapped: dict[str, Any] = {"raw": fields}

    for target, candidates in mapping.items():
        for candidate in candidates:
            hit = normalized.get(_normalize_key(candidate))
            if hit:
                mapped[target] = hit[1]
                break

    if isinstance(mapped.get("views"), (list, dict)):
        mapped["views"] = None
    elif mapped.get("views") is not None:
        try:
            mapped["views"] = float(str(mapped["views"]).replace(",", ""))
        except ValueError:
            mapped["views"] = None

    return mapped


def normalize_records(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        fields = record.get("fields", {})
        mapped = map_fields(fields)
        rows.append(
            {
                "airtable_id": record.get("id", ""),
                "title": mapped.get("title"),
                "url": mapped.get("url"),
                "publish_date": mapped.get("publish_date"),
                "views": mapped.get("views"),
                "author": mapped.get("author"),
                "section": mapped.get("section"),
                "topic": mapped.get("topic"),
                "raw_fields": fields,
            }
        )
    return rows


def save_exports(rows: list[dict], table_name: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "synced_at": utc_now(),
        "table": table_name,
        "count": len(rows),
        "records": rows,
    }
    latest = EXPORT_DIR / "latest.json"
    latest.write_text(json.dumps(payload, indent=2))
    return latest


def upsert_sqlite(rows: list[dict]) -> int:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS article_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airtable_id TEXT NOT NULL UNIQUE,
                title TEXT,
                url TEXT,
                publish_date TEXT,
                views REAL,
                author TEXT,
                section TEXT,
                topic TEXT,
                raw_fields TEXT,
                synced_at TEXT NOT NULL
            )
            """
        )
        synced_at = utc_now()
        count = 0
        for row in rows:
            conn.execute(
                """
                INSERT INTO article_performance (
                    airtable_id, title, url, publish_date, views, author, section, topic,
                    raw_fields, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(airtable_id) DO UPDATE SET
                    title=excluded.title,
                    url=excluded.url,
                    publish_date=excluded.publish_date,
                    views=excluded.views,
                    author=excluded.author,
                    section=excluded.section,
                    topic=excluded.topic,
                    raw_fields=excluded.raw_fields,
                    synced_at=excluded.synced_at
                """,
                (
                    row["airtable_id"],
                    row.get("title"),
                    row.get("url"),
                    str(row.get("publish_date") or ""),
                    row.get("views"),
                    row.get("author"),
                    row.get("section"),
                    row.get("topic"),
                    json.dumps(row.get("raw_fields") or {}),
                    synced_at,
                ),
            )
            count += 1
    return count


def sync_airtable() -> dict:
    cfg = airtable_config()
    table_name = cfg["table_name"]
    if not table_name:
        raise SystemExit(
            "Missing AIRTABLE_TABLE_NAME. Run: python3 scripts/sync_airtable.py --list-tables"
        )

    raw_records = fetch_records(
        cfg["token"],
        cfg["base_id"],
        table_name,
        cfg["view_name"],
    )
    rows = normalize_records(raw_records)
    export_path = save_exports(rows, table_name)
    sqlite_count = upsert_sqlite(rows)
    return {
        "records": len(rows),
        "export_path": str(export_path),
        "sqlite_rows": sqlite_count,
        "table": table_name,
        "view": cfg["view_name"] or "(default)",
    }


def analyze_performance(limit: int = 15) -> dict:
    init_db()
    with connect() as conn:
        try:
            rows = conn.execute(
                """
                SELECT title, url, publish_date, views, author, section, topic
                FROM article_performance
                WHERE views IS NOT NULL
                ORDER BY views DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) AS n, AVG(views) AS avg_views, MAX(views) AS max_views FROM article_performance WHERE views IS NOT NULL"
            ).fetchone()
        except sqlite3.OperationalError:
            raise SystemExit(
                "No Airtable data yet. Run: python3 scripts/sync_airtable.py --sync"
            ) from None

    top = [dict(row) for row in rows]
    return {
        "total_with_views": total["n"],
        "avg_views": round(total["avg_views"] or 0, 1),
        "max_views": total["max_views"],
        "top_articles": top,
    }
