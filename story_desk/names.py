"""Extract real people, events, and interview formats from headlines."""

from __future__ import annotations

import re

ORG_BLOCKLIST = (
    "symphony", "orchestra", "news", "express", "map", "wire", "fresh",
    "company", "department", "school district", "university", "college",
    "police", "court", "committee", "council", "association", "foundation",
    "network", "times", "post", "journal", "magazine", "report", "reads",
    "league", "commissioner", "commish", "digital fashion", "bread", "latin american",
)

BAD_NAMES = {
    "here", "this", "that", "what", "when", "where", "how", "why", "who",
    "youtube", "youtuber", "tiktok", "instagram", "facebook", "league",
    "digital fashion acceleration", "fashion acceleration", "latin american trump",
    "bread zeppelin", "culture map", "culturemap dallas", "gen z", "hellofresh",
    "nfl commish", "exclusive", "notebook", "festival", "report", "reports",
    "source", "parent", "student", "organizer", "creator", "activist", "influencer",
    "san angelo", "team czechia", "best dallas", "colombian president",
    "north texas", "fort worth", "world cup", "is here", "talk street", "and he",
    "george washington", "abraham lincoln", "jimmy kimmel", "sky news",
    "sees tesla", "christopher nolan",
}

SKIP_NAMES = {
    "Fox News", "Daily Wire", "White House", "Supreme Court", "New York",
    "Los Angeles", "San Francisco", "United States", "North Texas",
    "Fort Worth", "Plano Symphony Orchestra", "HelloFresh", "Gen Z",
}

EVENT_PATTERNS = [
    (re.compile(r"\b(in concert|concert with)\b", re.I), "concert"),
    (re.compile(r"\b(opening date|grand opening|opens|opening)\b", re.I), "opening"),
    (re.compile(r"\b(summit|conference|festival|parade|expo|fair)\b", re.I), "event"),
    (re.compile(r"\b(world cup|fifa|game day|watch party)\b", re.I), "sporting event"),
    (re.compile(r"\b(protest|rally|march|demonstration)\b", re.I), "protest"),
]

DALLAS_MARKERS = (
    "dallas", "dfw", "fort worth", "plano", "frisco", "arlington", "mckinney",
    "irving", "north texas", "deep ellum", "uptown", "smu",
)

# Handles and special creator names
HANDLE_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z0-9]*(?:Speed|Boy|Girl|Tube|Tok|Plays|Gaming)[A-Za-z0-9]*)\b"
)

APOST = r"[''\u2019]"

COMMON_WORDS = {
    "adapting", "book", "reacts", "report", "host", "news", "street", "talk",
    "landman", "creator", "month", "here", "best", "team", "digital",
    "fashion", "acceleration", "opening", "sets", "how", "why", "what", "sees", "tesla",
}

PERSON_PATTERNS = [
    (re.compile(r"\bhost\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b", re.I), 10),
    (re.compile(r"\bco-creator\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b", re.I), 10),
    (re.compile(r"^(?:YouTuber|TikToker|Influencer|Creator|Podcaster)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"), 9),
    (re.compile(rf"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})\s+(?:Built|Creates|Launched|Started)\b"), 9),
    (re.compile(r"\bfounder\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", re.I), 9),
    (re.compile(r"\b(?:President|Senator|Rep\.|Governor)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b"), 8),
    (re.compile(rf"[—–-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?){APOST}s\b"), 8),
    (re.compile(rf"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?){APOST}s\b"), 7),
    (re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+in\s+Concert\b"), 8),
    (re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:says|said|declines|speaks out|outlines|describes|sparked|reacts)\b"), 7),
    (re.compile(r"\b(?:Commish|Commissioner)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b"), 8),
    (re.compile(r"(?:Exclusive\s+[—-]\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+):"), 6),
]


def _clean_name(raw: str) -> str:
    name = re.sub(r"\s+", " ", raw.strip(" '\"–—-|"))
    name = re.sub(r"\s+(Outlines|Says|on|in|with|goes|Gets|Declines).*$", "", name, flags=re.I)
    return name.strip()


def _is_person_name(name: str) -> bool:
    if not name or len(name) < 3:
        return False
    if name in SKIP_NAMES:
        return False
    lowered = name.lower()
    if lowered in BAD_NAMES:
        return False
    if any(org in lowered for org in ORG_BLOCKLIST):
        return False
    if any(skip in name for skip in (" News", " Podcast", " Show", " Express")):
        return False
    if re.match(r"^(The|A|An|Here's|How|What|Why|When|Where|This|That)\b", name, re.I):
        return False
    # Require full first+last for generic capitalized pairs, unless handle-like
    words = name.split()
    if any(w.lower() in COMMON_WORDS for w in words):
        return False
    if len(words) == 1 and not HANDLE_PATTERN.fullmatch(name):
        return False
    if len(words) == 2 and words[0].lower() in {"latin", "digital", "bread", "nfl", "best", "team", "san", "colombian"}:
        return False
    if words[0].lower() in {"team", "best", "san", "digital", "fashion", "pride", "talk"}:
        return False
    if lowered.startswith("and "):
        return False
    return True


def extract_people(title: str, summary: str = "") -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()

    def add(name: str, source: str, weight: int = 5) -> None:
        name = _clean_name(name)
        if not _is_person_name(name):
            return
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        found.append({"name": name, "source": source, "weight": weight})

    # Handles first (IShowSpeed, etc.)
    for match in HANDLE_PATTERN.finditer(title):
        add(match.group(1), "handle", 9)

    for text, source in ((title, "title"), (summary, "summary")):
        if not text:
            continue
        if source == "title" and re.match(r"^(Here'?s|This is|How much|What|Why)\b", text, re.I):
            continue
        summary_boost = 2 if source == "summary" else 0
        for pattern, weight in PERSON_PATTERNS:
            for match in pattern.finditer(text):
                add(match.group(1), source, weight + summary_boost)

    found.sort(key=lambda p: (-p["weight"], 0 if p["source"] == "summary" else 1))
    return found


def detect_event(title: str, summary: str = "") -> dict | None:
    text = f"{title} {summary}"
    if "book on" in text or "adaptation" in text:
        return None  # force MOTS or event unless co-creator extracted
    if re.search(r"\b(arrives in|watch party|watch parties|world cup|fifa)\b", text, re.I):
        event_name = title.split(" - ")[0][:90]
        return {"type": "sporting event", "name": event_name, "title": title}
    if re.search(r"\b(celebrate|celebration|festival|parade)\b", text, re.I):
        event_name = title.split(" - ")[0][:90]
        return {"type": "event", "name": event_name, "title": title}
    if re.search(r"\bpride month\b", text, re.I) and not re.search(r"\bad\b|\bbrand\b|\bcompany\b|\bcrosses line\b", text, re.I):
        event_name = title.split(" - ")[0][:90]
        return {"type": "event", "name": event_name, "title": title}
    if re.search(r"\b(boys and girls|club|nonprofit|fundraiser)\b", text, re.I):
        return {"type": "event", "name": title.split(" - ")[0][:90], "title": title}
    for pattern, event_type in EVENT_PATTERNS:
        if pattern.search(text):
            event_name = re.split(r"\s+[\-|–|]\s+", title)[0].strip()
            event_name = re.sub(r"\s+-\s+[A-Z][a-z].*$", "", event_name)
            return {"type": event_type, "name": event_name, "title": title}
    return None


def _dallas_place(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    places = {
        "irving": "Irving",
        "plano": "Plano",
        "frisco": "Frisco",
        "arlington": "Arlington",
        "deep ellum": "Deep Ellum, Dallas",
        "uptown": "Uptown Dallas",
        "fort worth": "Fort Worth",
        "mckinney": "McKinney",
        "smu": "SMU campus, Dallas",
    }
    for key, label in places.items():
        if key in text:
            return label
    return "Dallas–Fort Worth"


def build_interview_plan(story: dict, pitch_type: str) -> dict:
    title = story["title"]
    summary = story.get("summary", "")
    people = extract_people(title, summary)
    event = detect_event(title, summary)
    place = _dallas_place(title, summary)

    # Local human-interest without a clear name in the headline
    local_subject = re.search(
        r"\b(Dallas|DFW|Fort Worth|Plano|Frisco|Irving)\s+(Man|Woman|mom|dad|couple)\b",
        title,
        re.I,
    )
    if local_subject and (
        not people
        or people[0].get("weight", 0) < 8
        or any(w in people[0]["name"].lower() for w in ("tesla", "sees"))
    ):
        label = local_subject.group(0).title()
        return {
            "format": "named",
            "format_label": "Named interview",
            "name": f"{label} (full name in source article)",
            "role": "Local subject",
            "hook": "Human-interest local story — open the source link for names, then request interview.",
            "outreach": "Read the linked story for names/contact; reach out via station or Facebook.",
            "is_suggested": False,
        }

    if re.match(r"^Why\b", title, re.I) and not any(p.get("weight", 0) >= 9 for p in people):
        return _man_on_street_plan(title, summary, pitch_type, place)

    if people and people[0].get("weight", 0) >= 7:
        person = people[0]
        role = _guess_role(title, summary, person["name"])
        return {
            "format": "named",
            "format_label": "Named interview",
            "name": person["name"],
            "role": role,
            "hook": _person_hook(person["name"], title, summary, role),
            "outreach": _outreach_for(person["name"], title, summary, role),
            "is_suggested": False,
        }

    if event:
        return _event_plan(title, summary, event, place)

    return _man_on_street_plan(title, summary, pitch_type, place)


def _event_plan(title: str, summary: str, event: dict, place: str) -> dict:
    if event["type"] == "concert":
        return {
            "format": "event",
            "format_label": "Attend event",
            "name": f"Attend: {event['name']}",
            "role": "Interview artist + 2–3 concertgoers on-site",
            "hook": "Show up at the performance — get quotes from attendees on why this moment matters locally.",
            "outreach": f"Get venue/time from source link; request press access or buy tickets in {place}.",
            "is_suggested": False,
        }
    if event["type"] == "opening":
        store = _opening_subject(title)
        return {
            "format": "event",
            "format_label": "Attend event",
            "name": f"Attend: {store} opening",
            "role": "Opening-day interviews",
            "hook": f"Be there for opening day — interview shoppers and staff about what it means for {place}.",
            "outreach": "Arrive early; grab 3 quick man-on-the-street reactions outside.",
            "is_suggested": False,
        }
    if event["type"] in ("sporting event", "event"):
        if "watch party" in f"{title} {summary}".lower() or "restaurant" in f"{title} {summary}".lower():
            return {
                "format": "event",
                "format_label": "Attend event",
                "name": f"Attend: {event['name'][:80]}",
                "role": "Bar/restaurant interviews + fan MOTS",
                "hook": f"Hit a listed watch-party spot in {place}; interview fans and one manager on the vibe.",
                "outreach": "Pick 1–2 venues from the roundup; no RSVP needed — show up during a match window.",
                "is_suggested": False,
            }
        return {
            "format": "event",
            "format_label": "Attend event",
            "name": f"Attend: {event['name'][:80]}",
            "role": "On-the-ground interviews",
            "hook": f"Cover the scene in {place} — interview arrivals, fans, or locals on camera.",
            "outreach": "Confirm time/location from source; bring mic for quick hits.",
            "is_suggested": False,
        }
    return {
        "format": "event",
        "format_label": "Attend event",
        "name": f"Attend: {event['name'][:80]}",
        "role": "On-the-ground interviews",
        "hook": f"Cover the scene in {place}.",
        "outreach": "Confirm details from source link.",
        "is_suggested": False,
    }


def _opening_subject(title: str) -> str:
    if "h-e-b" in title.lower() or "heb" in title.lower():
        return "H-E-B Irving"
    m = re.search(r"^(.{10,60}?)\s+(?:opens|opening|sets opening)", title, re.I)
    return m.group(1).strip() if m else title.split(" - ")[0][:60]


def _man_on_street_plan(title: str, summary: str, pitch_type: str, place: str) -> dict:
    text = f"{title} {summary}".lower()
    short_title = title.split(" - ")[0][:80]

    if "rent" in text or "housing" in text or "apartment" in text:
        location = "Deep Ellum or Uptown Dallas apartment corridor"
        question = "Are rent drops actually helping you, or is DFW still unaffordable?"
    elif "bread zeppelin" in text or "restaurant" in text or "baguette" in text:
        location = f"Frisco restaurant row / the new Bread Zeppelin location"
        question = "Would you wait in line for a viral food trend — or is it overhyped?"
    elif "summer job" in text or "gen z" in text:
        location = f"SMU or UT Dallas campus"
        question = "Are you able to find a summer job this year — and what's changed?"
    elif "influencer" in text or "viral" in text or "algorithm" in text or "fashion" in text:
        location = f"Bishop Arts or Deep Ellum, {place}"
        question = "Are algorithm-driven trends changing how you dress, post, or shop?"
    elif "pride" in text or "celebrate" in text:
        location = f"Pride events across {place} (check parade/festival schedule)"
        question = "What does Pride Month mean to you in Dallas this year?"
    elif "boys and girls" in text or "club" in text:
        location = "Boys & Girls Clubs of Dallas (see NBC 5 segment location)"
        question = "How is this program changing kids' lives in Dallas?"
    elif "ad" in text or "brand" in text:
        location = f"Busy shopping center in {place}"
        question = "Do brands go too far with culture-war ads — or is backlash overblown?"
    elif "hollywood" in text or "acting" in text or "beauty" in text:
        location = f"Deep Ellum or Los Colinas, {place}"
        question = "Has Hollywood's beauty obsession changed what you expect from actors and influencers?"
        location = f"Sports bar in {place} during primetime"
        question = "Are you paying more or cutting cords because of new streaming deals?"
    elif pitch_type == "dallas_local":
        location = place
        question = f"What do locals think about: {short_title}?"
    else:
        location = f"{place} (high-foot-traffic area)"
        question = f"Ask 5 people how this story lands locally: {short_title}"

    return {
        "format": "mots",
        "format_label": "Man-on-the-street",
        "name": f"Man-on-the-street — {location}",
        "role": "5 quick interviews (30–60 sec each)",
        "hook": question,
        "outreach": f"Film at {location}; get first name, age, neighborhood on camera.",
        "is_suggested": False,
    }


def _guess_role(title: str, summary: str, name: str) -> str:
    text = f"{title} {summary}".lower()
    if "founder" in text and name.lower() in text:
        return "Founder / activist"
    if "youtuber" in text or "youtube" in text or "ben" in name.lower() or HANDLE_PATTERN.fullmatch(name):
        return "YouTuber / creator"
    if "influencer" in text or "tiktok" in text or "instagram" in text:
        return "Influencer / creator"
    if "concert" in text or "musician" in text or "performer" in text:
        return "Performer"
    if "activist" in text:
        return "Activist"
    if "reporter" in text:
        return "Reporter"
    if "commish" in text or "commissioner" in text:
        return "Sports/media executive"
    if "president" in text or "senator" in text or "representative" in text:
        return "Political figure"
    if HANDLE_PATTERN.fullmatch(name):
        return "Creator / streamer"
    return "Source"


def _person_hook(name: str, title: str, summary: str, role: str) -> str:
    if summary and name.lower() in summary.lower():
        idx = summary.lower().find(name.lower())
        snippet = summary[max(0, idx - 20) : idx + 120].strip()
        return f"Ask {name} ({role}): {snippet}"
    return f"Interview {name} directly on: {title.split(' - ')[0]}"


def _outreach_for(name: str, title: str, summary: str, role: str) -> str:
    handle = re.sub(r"[^a-zA-Z0-9]", "", name)
    if role in ("YouTuber", "Influencer / creator", "Creator / streamer"):
        return f"Search X/Instagram/YouTube for @{handle} or '{name}'; DM or email via link in bio."
    if role == "Performer":
        return f"Contact {name}'s publicist via venue listing, or Instagram DMs before show day."
    if role in ("Founder / activist", "Activist"):
        return f"Search '{name}' + organization name from story; DM on X or contact via org website."
    if role == "Sports/media executive":
        return f"Request comment via NFL/league PR; pair with local sports bar MOTS for fan reaction."
    return f"Google '{name}' + recent news; check X/LinkedIn for verified account."
