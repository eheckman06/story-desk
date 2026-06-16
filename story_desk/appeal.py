"""National vs hyper-local appeal for a national culture/media beat."""

from __future__ import annotations

DALLAS_MARKERS = (
    "dallas", "dfw", "fort worth", "plano", "frisco", "arlington", "mckinney",
    "irving", "north texas", "deep ellum", "uptown", "smu", "collin county", "tarrant county",
)

INFLUENCER_MARKERS = (
    "influencer", "tiktok", "youtube", "creator", "viral", "instagram",
    "podcast", "streamer", "content creator", "youtuber",
)

NATIONAL_APPEAL_MARKERS = (
    "viral", "backlash", "national", "nationwide", "trending", "controversy",
    "lawsuit", "arrested", "indicted", "banned", "culture war", "speaks out",
    "firestorm", "debate", "outrage", "investigation", "investigates",
    "cancel", "cancelled", "canceled", "parents fear", "chilling effect",
    "free speech", "detransition", "detransitioner", "school board",
    "world cup", "fifa", "mlb", "christians", "tradwife", "gen z",
    "across the country", "americans", "u.s.", " united states",
)

HYPERLOCAL_MARKERS = (
    "debuts", "debut", "opens new", "grand opening", "new location",
    "restaurant", "lounge", "eatery", "cafe", "brewery", "steak & seafood",
    "fortune 500", "terminal c", "new gates", "airport expansion", "airport opens",
    "murals celebrating", "preston hollow", "scores new", "expands to new",
    "playground for kids", "soft serve", "symphony orchestra", "in concert with",
    "sports lounge", "discount fashion", "store to open", "matcha brings",
    "sneak-peek", "resort before it opens", "foodie favorite", "brewing culture one cup",
)


def story_text(story: dict) -> str:
    return f"{story.get('title', '')} {story.get('summary', '')}".lower()


def has_dallas_geo(text: str) -> bool:
    return any(m in text for m in DALLAS_MARKERS)


def has_national_appeal(text: str) -> bool:
    if any(m in text for m in INFLUENCER_MARKERS):
        return True
    return any(m in text for m in NATIONAL_APPEAL_MARKERS)


def is_too_local_for_national(story: dict) -> bool:
    """True when a story lacks a hook for a national audience."""
    text = story_text(story)
    if has_national_appeal(text):
        return False
    if any(m in text for m in HYPERLOCAL_MARKERS):
        return True
    if not has_dallas_geo(text):
        return False
    # Generic DFW dateline with no conflict, creator, or trend signal.
    return not any(
        m in text
        for m in ("backlash", "viral", "influencer", "creator", "protest", "lawsuit", "banned")
    )


def national_appeal_bonus(story: dict) -> float:
    text = story_text(story)
    bonus = 0.0
    if has_national_appeal(text):
        bonus += 12
    if has_dallas_geo(text) and has_national_appeal(text):
        bonus += 8
    return bonus


def hyperlocal_penalty(story: dict) -> float:
    return 35.0 if is_too_local_for_national(story) else 0.0
