"""Extract and score potential interview subjects from headlines."""

from __future__ import annotations

import re

NAME_PATTERN = re.compile(
    r"(?:"
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b(?:\s+(?:says|said|speaks out|told|claims|warns|shared|moved|rejected|attacked|indicted|faces|will no longer|describes))"
    r"|"
    r"(?:Exclusive\s+[—-]\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}):"
    r")"
)

ROLE_HINTS = {
    "influencer": "Influencer / creator",
    "youtuber": "YouTuber",
    "student": "Student",
    "parent": "Parent",
    "reporter": "Reporter",
    "detransitioner": "Detransitioner",
    "family": "Family member",
    "teacher": "Teacher",
    "organizer": "Organizer",
    "veteran": "Veteran",
    "hairstylist": "Everyday worker",
    "homeowner": "Local resident",
    "conservative": "Conservative voice",
    "activist": "Activist",
    "podcast": "Podcaster",
}

SKIP_NAMES = {
    "Fox News",
    "Daily Wire",
    "White House",
    "Supreme Court",
    "New York",
    "Los Angeles",
    "San Francisco",
    "Operation Epic",
    "United States",
    "Supreme Leader",
    "Breitbart News",
    "Breitbart News Saturday",
    "Live Action",
    "Notebook",
    "Festival Horror",
}

BAD_SINGLE_NAMES = {
    "Notebook", "Exclusive", "Festival", "Update", "Analysis", "Opinion",
    "Live", "Breaking", "Watch", "Video", "Report", "Reports",
}


def _guess_role(text: str) -> str:
    lowered = text.lower()
    for keyword, role in ROLE_HINTS.items():
        if keyword in lowered:
            return role
    return "Source with personal stake"


def _contact_hint(name: str, text: str) -> str:
    lowered = text.lower()
    if "twitter" in lowered or "x.com" in lowered:
        return "Search X/Twitter for recent posts; DM if public."
    if "instagram" in lowered or "tiktok" in lowered:
        return "Likely reachable via Instagram/TikTok DMs or agent."
    if "student" in lowered or "parent" in lowered or "family" in lowered:
        return "Reach through local school board contacts, organizers, or Fox tips line."
    if "reporter" in lowered or "tpusa" in lowered:
        return "Often public on X; may respond to journalist DM."
    return "Google name + recent news; check X/LinkedIn for direct outreach."


def _why_elizabeth(role: str, theme_hits: str) -> str:
    themes = theme_hits.lower()
    if "culture" in themes or "social media" in themes:
        return "Matches your culture/influencer lane — strong quote potential for Fox Digital."
    if "texas" in themes or "local" in themes:
        return "Texas/local human interest is a core part of your byline."
    if "free speech" in themes:
        return "First-person campus or cancel-culture voice — your Chloe Cole / UVU beat."
    if "border" in themes or "ice" in themes:
        return "On-the-ground protest or border character — similar to your Savanah Hernandez coverage."
    if "everyday" in themes:
        return "Everyday American with a bold POV — your Kentucky farmland / Dubai stylist formula."
    if "gender" in themes or "detransition" in themes:
        return "Fits your detransitioner and gender-policy coverage."
    if "conservative" in themes:
        return "Conservative voice in a culturally charged moment — your Amir Odom / campus lane."
    return f"Strong {role.lower()} angle aligned with your Fox Digital profile."


def _subject_hook(name: str, title: str, summary: str) -> str:
    text = f"{title}. {summary}".strip()
    if len(text) <= 220:
        return text
    return text[:217] + "..."


def extract_subjects(story: dict, themes: list[dict]) -> list[dict]:
    text = f"{story['title']} {story.get('summary', '')}"
    subjects: list[dict] = []
    seen: set[str] = set()

    for match in NAME_PATTERN.finditer(story["title"] + " " + story.get("summary", "")):
        name = (match.group(1) or match.group(2) or "").strip()
        if not name:
            continue
        title = story["title"]
        if re.match(rf"^{re.escape(name)}\s*:", title):
            continue
        if any(skip.lower() in name.lower() for skip in (" News", " Podcast", " Show", " Saturday", " Horror", " Exclusive")):
            continue
        if name in SKIP_NAMES or name in seen:
            continue
        if name in BAD_SINGLE_NAMES:
            continue
        if len(name.split()) == 1 and name.lower() in BAD_SINGLE_NAMES:
            continue
        if len(name.split()) == 1 and name.lower() in {"president", "senator", "representative", "governor"}:
            continue
        seen.add(name)

        role = _guess_role(text)
        theme_hits = story.get("theme_hits", "")
        interview_bonus = 0
        lowered = text.lower()
        for theme in themes:
            if any(signal in lowered for signal in theme.get("interview_signals", [])):
                interview_bonus += 6

        if role != "Source with personal stake":
            interview_bonus += 8
        if "speaks out" in lowered or "no regrets" in lowered or "rejected" in lowered:
            interview_bonus += 10

        score = round(story.get("score", 0) * 0.65 + interview_bonus, 1)
        subjects.append(
            {
                "name": name,
                "role": role,
                "story_url": story["url"],
                "story_title": story["title"],
                "hook": _subject_hook(name, story["title"], story.get("summary", "")),
                "why_elizabeth": _why_elizabeth(role, theme_hits),
                "contact_hint": _contact_hint(name, text),
                "score": score,
                "theme_hits": theme_hits,
            }
        )

    # Fallback: if no named person, synthesize a subject archetype from the headline.
    if not subjects and story.get("score", 0) >= 25:
        fallback_name = _fallback_subject_name(story)
        if fallback_name:
            subjects.append(
                {
                    "name": fallback_name,
                    "role": _guess_role(text),
                    "story_url": story["url"],
                    "story_title": story["title"],
                    "hook": _subject_hook(fallback_name, story["title"], story.get("summary", "")),
                    "why_elizabeth": _why_elizabeth(_guess_role(text), story.get("theme_hits", "")),
                    "contact_hint": _contact_hint(fallback_name, text),
                    "score": round(story.get("score", 0) * 0.55, 1),
                    "theme_hits": story.get("theme_hits", ""),
                }
            )

    return subjects


def _fallback_subject_name(story: dict) -> str | None:
    text = f"{story['title']} {story.get('summary', '')}".lower()
    if "student" in text:
        return "Unnamed student at center of story"
    if "parent" in text or "family" in text:
        return "Family speaking out in local report"
    if "protest" in text:
        return "Protest participant or citizen on scene"
    if "school" in text:
        return "Parent or student organizer"
    if "influencer" in text or "creator" in text:
        return "Creator named in viral coverage"
    return None


def rank_subjects(stories: list[dict], themes: list[dict], limit: int = 20) -> list[dict]:
    subjects: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for story in stories:
        for subject in extract_subjects(story, themes):
            key = (subject["name"], subject["story_url"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            subjects.append(subject)

    subjects.sort(key=lambda item: item["score"], reverse=True)
    return subjects[:limit]
