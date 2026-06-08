"""Story desk database helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "story_desk.db"
SCHEMA_PATH = ROOT / "schema.sql"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


def story_exists(conn: sqlite3.Connection, url: str) -> bool:
    row = conn.execute("SELECT 1 FROM stories WHERE url = ?", (url,)).fetchone()
    return row is not None


def insert_story(conn: sqlite3.Connection, story: dict) -> int | None:
    if story_exists(conn, story["url"]):
        return None
    cur = conn.execute(
        """
        INSERT INTO stories (
            title, url, summary, source_id, source_name, published_at,
            fetched_at, score, theme_hits, angle, why_now
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            story["title"],
            story["url"],
            story.get("summary", ""),
            story["source_id"],
            story["source_name"],
            story.get("published_at"),
            utc_now(),
            story.get("score", 0),
            story.get("theme_hits", ""),
            story.get("angle", ""),
            story.get("why_now", ""),
        ),
    )
    return cur.lastrowid


def insert_interview_subject(conn: sqlite3.Connection, subject: dict) -> int | None:
    row = conn.execute(
        "SELECT id FROM interview_subjects WHERE name = ? AND story_url = ?",
        (subject["name"], subject.get("story_url", "")),
    ).fetchone()
    if row:
        return None
    cur = conn.execute(
        """
        INSERT INTO interview_subjects (
            name, role, story_url, story_title, hook, why_elizabeth,
            contact_hint, score, theme_hits, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject["name"],
            subject.get("role", ""),
            subject.get("story_url", ""),
            subject.get("story_title", ""),
            subject.get("hook", ""),
            subject.get("why_elizabeth", ""),
            subject.get("contact_hint", ""),
            subject.get("score", 0),
            subject.get("theme_hits", ""),
            utc_now(),
        ),
    )
    return cur.lastrowid


def record_daily_pick(conn: sqlite3.Connection, pick: dict) -> None:
    conn.execute(
        """
        INSERT INTO daily_picks (pick_date, pick_type, rank_num, title, detail, score, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pick["pick_date"],
            pick["pick_type"],
            pick["rank"],
            pick["title"],
            pick["detail"],
            pick.get("score", 0),
            pick.get("source_url", ""),
        ),
    )


def recent_story_urls(conn: sqlite3.Connection, days: int = 14) -> set[str]:
    rows = conn.execute(
        """
        SELECT url FROM stories
        WHERE fetched_at >= datetime('now', ?)
        """,
        (f"-{days} days",),
    ).fetchall()
    return {row["url"] for row in rows}
