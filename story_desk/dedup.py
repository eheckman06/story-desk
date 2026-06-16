"""Cross-headline dedup — same person/story, different URL or rewrite."""

from __future__ import annotations

import re

GENERIC_DEDUP_TOKENS = frozenset({
    "about", "across", "after", "again", "ahead", "amid", "arrested", "backlash",
    "bond", "builds", "culture", "creator", "dallas", "debuts", "details", "dfw",
    "everything", "excitement", "explored", "fans", "fort", "held", "influencer",
    "know", "local", "media", "million", "national", "need", "news", "north",
    "opener", "party", "prepares", "social", "team", "texas", "threat", "trend",
    "under", "viral", "watch", "world", "worth", "youtuber", "youtube",
    "using", "apps", "including", "from", "over", "into", "their", "they",
    "what", "when", "where", "which", "while", "will", "with", "your",
})


def substantive_tokens(title: str) -> set[str]:
    words = re.sub(r"[^a-z0-9\s]", " ", title.lower()).split()
    return {
        w
        for w in words
        if len(w) > 2 and w not in GENERIC_DEDUP_TOKENS
    }


def same_story_subject(a: str, b: str, *, min_overlap: int = 2) -> bool:
    """True when two headlines cover the same person or story arc."""
    overlap = substantive_tokens(a) & substantive_tokens(b)
    return len(overlap) >= min_overlap


def is_repeat_of_prior(title: str, prior_titles: list[str]) -> bool:
    return any(same_story_subject(title, prior) for prior in prior_titles)
