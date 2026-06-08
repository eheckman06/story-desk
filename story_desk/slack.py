"""Send daily picks to Slack via incoming webhook."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date


def _webhook_url() -> str | None:
    return os.environ.get("SLACK_WEBHOOK_URL", "").strip() or None


def _truncate(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_slack_payload(
    stories: list[dict],
    subjects: list[dict],
    run_date: date,
    markdown_path: str,
) -> dict:
    date_label = run_date.strftime("%A, %B %d, %Y")
    story_lines = []
    for idx, story in enumerate(stories, start=1):
        story_lines.append(f"*{idx}. {story['title']}*")
        story_lines.append(f"   {story.get('angle', '')}")

    subject_lines = []
    for idx, subject in enumerate(subjects, start=1):
        subject_lines.append(f"*{idx}. {subject['name']}* ({subject.get('role', 'Source')})")
        subject_lines.append(f"   {_truncate(subject.get('hook', ''))}")

    story_text = "\n".join(story_lines) if story_lines else "_No strong story matches today._"
    subject_text = "\n".join(subject_lines) if subject_lines else "_No interview subjects extracted today._"

    return {
        "text": f"Here are story pitches — {date_label}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Here are story pitches"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Story Desk · {date_label}*\n2 story pitches and 2 interview subjects for your Fox Digital beat.",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Story picks*\n{story_text}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Interview subjects*\n{subject_text}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Full digest saved locally: `{markdown_path}`",
                    }
                ],
            },
        ],
    }


def send_slack_notification(
    stories: list[dict],
    subjects: list[dict],
    run_date: date,
    markdown_path: str,
) -> bool:
    webhook = _webhook_url()
    if not webhook:
        print("Slack: skipped (set SLACK_WEBHOOK_URL in data/.env)")
        return False

    payload = build_slack_payload(stories, subjects, run_date, markdown_path)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status != 200:
                print(f"Slack: unexpected status {response.status}")
                return False
        print("Slack: notification sent")
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Slack: HTTP error {exc.code}: {body}")
        return False
    except urllib.error.URLError as exc:
        print(f"Slack: request failed: {exc.reason}")
        return False
