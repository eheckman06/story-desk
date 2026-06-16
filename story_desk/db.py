"""Story desk database helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
import re
from datetime import date, datetime, timedelta, timezone
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


from story_desk.dedup import is_repeat_of_prior


def topic_key_from_title(title: str) -> str:
    """Stable fingerprint for deduping similar headlines across runs."""
    words = re.sub(r"[^a-z0-9\s]", " ", title.lower()).split()
    stop = {
        "the", "a", "an", "in", "at", "for", "to", "of", "and", "with", "on", "new", "says",
        "here", "this", "how", "much", "have", "has", "since", "2025", "2026",
    }
    tokens = [w for w in words if w not in stop and len(w) > 2][:8]
    return " ".join(sorted(tokens))


def pick_exclusions_for_date(run_date: date) -> tuple[set[str], set[str], list[str]]:
    """
    URLs, topic keys, and prior titles to skip so weekday runs stay fresh.

    Tue–Fri: exclude timely picks from Monday of this week through today (inclusive).
    Monday: exclude only the prior Tue–Fri window so Saturday/Sunday picks may repeat.
    Sat–Sun: exclude same-day picks only (weekend refresh).
    """
    weekday = run_date.weekday()
    run_iso = run_date.isoformat()

    if weekday == 0:
        start = (run_date - timedelta(days=6)).isoformat()
        end = (run_date - timedelta(days=3)).isoformat()
        clause = "pick_date >= ? AND pick_date <= ?"
        params: tuple[str, ...] = (start, end)
    elif weekday <= 4:
        week_monday = (run_date - timedelta(days=weekday)).isoformat()
        clause = "pick_date >= ? AND pick_date <= ?"
        params = (week_monday, run_iso)
    else:
        clause = "pick_date = ?"
        params = (run_iso,)

    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT source_url, title FROM daily_picks
            WHERE pick_type IN ('timely', 'pitch')
              AND source_url != ''
              AND {clause}
            """,
            params,
        ).fetchall()

    urls = {row["source_url"] for row in rows if row["source_url"]}
    titles = [row["title"] for row in rows if row["title"]]
    topics = {topic_key_from_title(title) for title in titles}
    return urls, topics, titles
