"""Daily story desk pipeline."""

from __future__ import annotations

from datetime import date

from story_desk.config_loader import load_sources, load_themes
from story_desk.db import connect, init_db, insert_interview_subject, insert_story, record_daily_pick
from story_desk.evergreen import pick_evergreen_pitches
from story_desk.fetch import fetch_all_feeds
from story_desk.interview import extract_subjects, rank_subjects
from story_desk.pitches import build_pitches
from story_desk.publish import publish_site
from story_desk.report import write_daily_outputs
from story_desk.scorer import rank_stories


def _merge_pitches(timely: list[dict], evergreen: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for pitch in timely:
        item = dict(pitch)
        item["source_kind"] = "timely"
        item["evergreen"] = False
        merged.append(item)
    for pitch in evergreen:
        item = dict(pitch)
        item["source_kind"] = "evergreen"
        item["evergreen"] = True
        merged.append(item)
    for idx, pitch in enumerate(merged, start=1):
        pitch["rank"] = idx
    return merged


def run_daily(run_date: date | None = None) -> dict:
    run_date = run_date or date.today()
    themes_cfg = load_themes()
    sources_cfg = load_sources()
    themes = themes_cfg["themes"]
    targets = themes_cfg["daily_targets"]
    timely_count = targets.get("timely", 7)
    evergreen_count = targets.get("evergreen", 3)
    pitch_target = targets.get("pitches", timely_count + evergreen_count)

    init_db()
    raw_stories = fetch_all_feeds(sources_cfg["rss_feeds"])
    ranked_stories = rank_stories(raw_stories, themes, limit=120)
    ranked_subjects = rank_subjects(ranked_stories, themes, limit=80)
    timely_pitches = build_pitches(ranked_stories, themes, limit=timely_count)
    evergreen_pitches = pick_evergreen_pitches(run_date, count=evergreen_count)
    pitches = _merge_pitches(timely_pitches, evergreen_pitches)[:pitch_target]

    with connect() as conn:
        for story in ranked_stories:
            insert_story(conn, story)
        for subject in ranked_subjects:
            insert_interview_subject(conn, subject)

        pick_date = run_date.isoformat()
        for pitch in pitches:
            record_daily_pick(
                conn,
                {
                    "pick_date": pick_date,
                    "pick_type": "pitch",
                    "rank": pitch["rank"],
                    "title": pitch["headline"],
                    "detail": f"{pitch['guest_name']} | {pitch['localize']}",
                    "score": pitch["score"],
                    "source_url": pitch.get("url", ""),
                },
            )
            if pitch.get("source_kind") == "timely":
                for subject in extract_subjects(
                    {
                        "title": pitch["headline"],
                        "summary": pitch.get("summary", ""),
                        "url": pitch.get("url", ""),
                        "theme_hits": pitch.get("themes", ""),
                        "score": pitch["score"],
                    },
                    themes,
                ):
                    insert_interview_subject(conn, subject)

    outputs = write_daily_outputs(pitches, run_date)
    site_dir = publish_site()

    return {
        "date": run_date.isoformat(),
        "fetched": len(raw_stories),
        "pitches": len(pitches),
        "timely": len(timely_pitches),
        "evergreen": len(evergreen_pitches),
        "site_dir": str(site_dir),
        **outputs,
    }
