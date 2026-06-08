"""Fetch headlines from configured RSS feeds."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.request import Request, urlopen

USER_AGENT = "StoryDesk/1.0 (+local research tool)"


def _strip_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_text(node: ET.Element | None, names: tuple[str, ...]) -> str:
    if node is None:
        return ""
    for child in node:
        if _local(child.tag) in names and child.text:
            return child.text.strip()
    return ""


def _find_link(node: ET.Element) -> str:
    for child in node:
        if _local(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            return href.strip()
        if child.text:
            return child.text.strip()
    return ""


def _parse_rss_items(root: ET.Element) -> list[dict]:
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = _first_text(item, ("title",))
        link = _first_text(item, ("link",)) or _find_link(item)
        summary = _first_text(item, ("description", "encoded"))
        published = _first_text(item, ("pubDate", "published", "updated"))
        if title and link:
            items.append(
                {
                    "title": _strip_html(title),
                    "url": link.strip(),
                    "summary": _strip_html(summary),
                    "published_at": _parse_date(published),
                }
            )
    return items


def _parse_atom_entries(root: ET.Element) -> list[dict]:
    items = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = _first_text(entry, ("title",))
        link = _find_link(entry)
        summary = _first_text(entry, ("summary", "content"))
        published = _first_text(entry, ("published", "updated"))
        if title and link:
            items.append(
                {
                    "title": _strip_html(title),
                    "url": link.strip(),
                    "summary": _strip_html(summary),
                    "published_at": _parse_date(published),
                }
            )
    return items


def fetch_feed(url: str, timeout: int = 20) -> list[dict]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()

    root = ET.fromstring(payload)
    tag = _local(root.tag).lower()
    if tag == "rss":
        return _parse_rss_items(root)
    if tag == "feed":
        return _parse_atom_entries(root)
    return []


def fetch_all_feeds(feeds: list[dict]) -> list[dict]:
    stories: list[dict] = []
    seen_urls: set[str] = set()

    for feed in feeds:
        try:
            items = fetch_feed(feed["url"])
        except Exception as exc:  # noqa: BLE001 - keep daily run resilient
            print(f"Warning: failed to fetch {feed['name']}: {exc}")
            continue

        for item in items:
            if item["url"] in seen_urls:
                continue
            seen_urls.add(item["url"])
            stories.append(
                {
                    **item,
                    "source_id": feed["id"],
                    "source_name": feed["name"],
                    "source_weight": float(feed.get("weight", 1.0)),
                }
            )
    return stories
