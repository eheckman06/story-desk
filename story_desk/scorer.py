"""Score stories against Elizabeth Heckman's beat."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from story_desk.appeal import (
    has_dallas_geo,
    has_national_appeal,
    hyperlocal_penalty,
    national_appeal_bonus,
    story_text,
)

FRESHNESS_BONUS = {
    6: 12,
    24: 8,
    48: 4,
}


def _hours_old(published_at: str | None) -> float | None:
    if not published_at:
        return None
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return max(delta.total_seconds() / 3600, 0)
    except ValueError:
        return None


def _freshness_bonus(hours: float | None) -> float:
    if hours is None:
        return 0
    for threshold, bonus in FRESHNESS_BONUS.items():
        if hours <= threshold:
            return bonus
    return 0


def _match_themes(text: str, themes: list[dict]) -> list[tuple[str, str, float]]:
    lowered = text.lower()
    hits: list[tuple[str, str, float]] = []
    for theme in themes:
        matched = [kw for kw in theme["keywords"] if kw.lower() in lowered]
        if matched:
            hits.append((theme["id"], theme["label"], theme["weight"] * len(matched)))
    return hits


def _story_angle(title: str, summary: str, themes: list[tuple[str, str, float]]) -> str:
    labels = [label for _, label, _ in themes[:3]]
    text = f"{title} {summary}".lower()
    if not labels:
        return "Monitor for a human-interest or culture angle with national stakes."
    if any("Dallas" in label or "DFW" in label for label in labels):
        if has_national_appeal(text):
            return "Texas/local dateline with national culture or influencer stakes — lead with the person in the conflict."
        return "DFW mention only — needs a national hook (viral moment, policy fight, named creator) before pitching."
    if any("Culture" in label or "social" in label.lower() for label in labels):
        return "National culture/social media story with a strong personal voice."
    if any("Media" in label or "platform" in label.lower() for label in labels):
        return "National media/platform trend — profile the creator or source driving it."
    if any("Free speech" in label for label in labels):
        return "Campus or public figure facing backlash — good for first-person interviews."
    if any("Border" in label for label in labels):
        return "Border/ICE story with on-the-ground characters or victims."
    if any("Everyday" in label for label in labels):
        return "Ordinary person making an unexpected or principled stand."
    return f"Strong fit for your {labels[0].lower()} coverage."


def _why_now(title: str, summary: str, hours: float | None) -> str:
    text = f"{title} {summary}".lower()
    if hours is not None and hours <= 12:
        return "Breaking in the last half-day — good window to own the human side before it gets crowded."
    if any(word in text for word in ("protest", "lawsuit", "canceled", "indicted", "viral")):
        return "Active news cycle with clear conflict and interview potential."
    if any(word in text for word in ("student", "school", "campus", "high school")):
        return "School-year culture clash with parents and students available locally."
    return "Timely enough to pitch with a fresh person-on-the-ground angle."


def score_story(story: dict, themes: list[dict]) -> dict:
    text = story_text(story)
    theme_hits = _match_themes(text, themes)
    theme_score = sum(weight for _, _, weight in theme_hits) * 10
    source_bonus = story.get("source_weight", 1.0) * 5
    hours = _hours_old(story.get("published_at"))
    freshness = _freshness_bonus(hours)

    # Prefer human-led headlines over pure process politics.
    human_bonus = 0
    human_markers = (
        "says", "family", "student", "influencer", "parent", "reporter",
        "speaks out", "moved to", "rejected", "viral", "attacked"
    )
    human_bonus += sum(4 for marker in human_markers if marker in text)

    influencer_markers = ("influencer", "tiktok", "creator", "viral", "youtube", "instagram")
    if any(m in text for m in influencer_markers):
        human_bonus += 10
    if any(m in text for m in ("culture", "media", "podcast", "streaming")):
        human_bonus += 6
    if has_dallas_geo(text) and has_national_appeal(text):
        human_bonus += 10

    penalty = hyperlocal_penalty(story)
    non_culture_dallas = (
        "airport", "terminal", "gate", "runway", "traffic", "highway", "weather",
        "forecast", "bond election", "property tax", "zoning"
    )
    if any(m in text for m in non_culture_dallas) and not has_national_appeal(text):
        penalty += 20

    if re.search(r"\b(says|warns|claims|slams|blasts|vows)\b.*\b(biden|trump|democrat|republican|homan|johnson)\b", text):
        penalty += 8
    if re.search(r"\b(nfl|goodell|hearing|testify|congress|senate|house)\b", text) and "broadcast" not in text and "streaming" not in text:
        penalty += 12
    if "vows" in text and not any(m in text for m in human_markers):
        penalty += 6

    score = round(
        theme_score + source_bonus + freshness + human_bonus + national_appeal_bonus(story) - penalty,
        1,
    )
    labels = [label for _, label, _ in theme_hits]

    return {
        **story,
        "score": max(score, 0),
        "theme_hits": ", ".join(labels),
        "angle": _story_angle(story["title"], story.get("summary", ""), theme_hits),
        "why_now": _why_now(story["title"], story.get("summary", ""), hours),
    }


def rank_stories(stories: list[dict], themes: list[dict], limit: int = 20) -> list[dict]:
    scored = [score_story(story, themes) for story in stories]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]
