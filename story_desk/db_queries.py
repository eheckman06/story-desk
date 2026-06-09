"""Query and export helpers for the story desk SQLite database."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from story_desk.db import connect, init_db

ROOT = Path(__file__).resolve().parents[1]
EXPORT_JSON = ROOT / "data" / "database.json"


def get_stats() -> dict:
    init_db()
    with connect() as conn:
        stories = conn.execute("SELECT COUNT(*) AS n FROM stories").fetchone()["n"]
        subjects = conn.execute("SELECT COUNT(*) AS n FROM interview_subjects").fetchone()["n"]
        picks = conn.execute("SELECT COUNT(*) AS n FROM daily_picks").fetchone()["n"]
        dates = [
            row["pick_date"]
            for row in conn.execute(
                "SELECT DISTINCT pick_date FROM daily_picks ORDER BY pick_date DESC"
            ).fetchall()
        ]
        top_source = conn.execute(
            """
            SELECT source_name, COUNT(*) AS n FROM stories
            GROUP BY source_name ORDER BY n DESC LIMIT 5
            """
        ).fetchall()
    return {
        "stories": stories,
        "subjects": subjects,
        "picks": picks,
        "pick_dates": dates,
        "top_sources": [{"name": r["source_name"], "count": r["n"]} for r in top_source],
    }


def _row_to_dict(row) -> dict:
    return dict(row)


def fetch_stories(limit: int = 500, min_score: float = 0) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, url, summary, source_name, published_at, fetched_at,
                   score, theme_hits, angle, why_now
            FROM stories
            WHERE score >= ?
            ORDER BY score DESC, fetched_at DESC
            LIMIT ?
            """,
            (min_score, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def fetch_subjects(limit: int = 300, min_score: float = 0) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, role, story_url, story_title, hook, why_elizabeth,
                   contact_hint, score, theme_hits, fetched_at
            FROM interview_subjects
            WHERE score >= ?
            ORDER BY score DESC, fetched_at DESC
            LIMIT ?
            """,
            (min_score, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def fetch_picks(limit: int = 500) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, pick_date, pick_type, rank_num, title, detail, score, source_url, created_at
            FROM daily_picks
            ORDER BY pick_date DESC, rank_num ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def export_database() -> dict:
    payload = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %I:%M %p").lstrip("0"),
        "stats": get_stats(),
        "stories": fetch_stories(),
        "subjects": fetch_subjects(),
        "picks": fetch_picks(),
    }
    EXPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_JSON.write_text(json.dumps(payload, indent=2))
    return payload
