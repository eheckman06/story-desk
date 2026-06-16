"""Build combined culture/media pitches with interview guests."""

from __future__ import annotations

from story_desk.appeal import has_dallas_geo, has_national_appeal, is_too_local_for_national, story_text
from story_desk.dedup import is_repeat_of_prior
from story_desk.names import build_interview_plan, extract_people

DALLAS_MARKERS = (
    "dallas", "dfw", "fort worth", "plano", "frisco", "arlington", "mckinney",
    "irving", "north texas", "deep ellum", "uptown", "smu", "collin county", "tarrant county",
)

INFLUENCER_MARKERS = (
    "influencer", "tiktok", "youtube", "creator", "viral", "instagram",
    "podcast", "streamer", "content creator",
)

CULTURE_MARKERS = (
    "culture", "media", "backlash", "cancel", "trend", "viral", "platform",
    "gen z", "social media", "hollywood", "streaming",
)


def _classify_pitch(story: dict) -> str:
    text = story_text(story)
    if any(m in text for m in INFLUENCER_MARKERS):
        return "influencer"
    if has_dallas_geo(text) and has_national_appeal(text):
        return "dallas_local"
    return "culture_media"


def _pitch_type_label(pitch_type: str) -> str:
    return {
        "dallas_local": "Dallas / DFW — national hook",
        "influencer": "Influencer / creator",
        "culture_media": "Culture / media trend",
    }.get(pitch_type, "Culture / media")


def _localize_note(story: dict, pitch_type: str) -> str:
    text = story_text(story)
    if pitch_type == "dallas_local":
        return "National story with a Texas dateline — interview the named source; don't pitch pure neighborhood news."
    if pitch_type == "influencer":
        if has_dallas_geo(text):
            return "Creator story with Dallas ties — profile the person driving the national conversation."
        return "National creator/platform story — interview the named influencer or expert, not local MOTS filler."
    if has_dallas_geo(text) and has_national_appeal(text):
        return "Optional Texas B-roll — only if the named national source is unavailable."
    return "National culture/media trend — lead with the person or platform driving the story nationwide."


def _is_on_brief(story: dict) -> bool:
    if is_too_local_for_national(story):
        return False
    text = story_text(story)
    has_influencer = any(m in text for m in INFLUENCER_MARKERS)
    has_culture = any(m in text for m in CULTURE_MARKERS)
    theme_hits = story.get("theme_hits", "").lower()
    has_theme = any(
        token in theme_hits
        for token in ("culture", "social", "media", "influencer")
    )
    if has_influencer or (has_culture and has_theme):
        return True
    return has_dallas_geo(text) and has_national_appeal(text)


def _topic_key(headline: str) -> str:
    from story_desk.db import topic_key_from_title

    return topic_key_from_title(headline)


def _interview_priority(story: dict, plan: dict) -> int:
    """Prefer pitches with real names, then events, then MOTS."""
    if plan["format"] == "named":
        return 3
    if plan["format"] == "event":
        return 2
    return 1


def build_pitches(
    stories: list[dict],
    themes: list[dict],
    limit: int = 10,
    *,
    exclude_urls: set[str] | None = None,
    exclude_topic_keys: set[str] | None = None,
    exclude_titles: list[str] | None = None,
) -> list[dict]:
    on_brief = [s for s in stories if _is_on_brief(s)]
    pool = on_brief if len(on_brief) >= limit else stories

    candidates: list[tuple[dict, dict, str, int]] = []
    for story in pool:
        pitch_type = _classify_pitch(story)
        plan = build_interview_plan(story, pitch_type)
        priority = _interview_priority(story, plan)
        score = story.get("score", 0) + priority * 8 + (5 if extract_people(story["title"], story.get("summary", "")) else 0)
        candidates.append((story, plan, pitch_type, score))

    candidates.sort(key=lambda item: item[3], reverse=True)

    pitches: list[dict] = []
    seen_urls: set[str] = set(exclude_urls or ())
    seen_topics: set[str] = set(exclude_topic_keys or ())
    seen_titles: list[str] = list(exclude_titles or ())
    type_counts = {"dallas_local": 0, "influencer": 0, "culture_media": 0}

    def _accept(story: dict) -> bool:
        if story["url"] in seen_urls:
            return False
        title = story["title"]
        if _topic_key(title) in seen_topics:
            return False
        if is_repeat_of_prior(title, seen_titles):
            return False
        return True

    def _remember(story: dict) -> None:
        seen_urls.add(story["url"])
        seen_topics.add(_topic_key(story["title"]))
        seen_titles.append(story["title"])

    for story, plan, pitch_type, _ in candidates:
        if not _accept(story):
            continue
        if pitch_type == "dallas_local" and type_counts[pitch_type] >= max(limit // 4 + 1, 2):
            continue
        if type_counts[pitch_type] >= max(limit // 3 + 1, 3):
            continue
        pitches.append(_make_pitch(len(pitches) + 1, story, pitch_type, plan))
        _remember(story)
        type_counts[pitch_type] += 1
        if len(pitches) >= limit:
            return pitches

    for story, plan, pitch_type, _ in candidates:
        if not _accept(story):
            continue
        pitches.append(_make_pitch(len(pitches) + 1, story, pitch_type, plan))
        _remember(story)
        if len(pitches) >= limit:
            break

    return pitches


def _make_pitch(rank: int, story: dict, pitch_type: str, plan: dict) -> dict:
    return {
        "rank": rank,
        "pitch_type": pitch_type,
        "pitch_type_label": _pitch_type_label(pitch_type),
        "headline": story["title"],
        "summary": story.get("summary", ""),
        "angle": story.get("angle", ""),
        "why_now": story.get("why_now", ""),
        "localize": _localize_note(story, pitch_type),
        "score": story.get("score", 0),
        "themes": story.get("theme_hits", ""),
        "source_name": story.get("source_name", ""),
        "url": story["url"],
        "guest_format": plan["format"],
        "guest_format_label": plan["format_label"],
        "guest_name": plan["name"],
        "guest_role": plan["role"],
        "guest_hook": plan["hook"],
        "guest_outreach": plan["outreach"],
        "guest_is_suggested": plan.get("is_suggested", False),
    }
