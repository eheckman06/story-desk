"""Generate markdown and HTML digests."""

from __future__ import annotations

import html
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "daily"
LATEST_HTML = ROOT / "data" / "latest.html"
LATEST_JSON = ROOT / "data" / "latest.json"


def write_daily_markdown(pitches: list[dict], run_date: date | None = None) -> Path:
    run_date = run_date or date.today()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{run_date.isoformat()}.md"

    lines = [
        f"# Story Desk — {run_date.strftime('%A, %B')} {run_date.day}, {run_date.year}",
        "",
        "10 culture/media pitches — Dallas/DFW local and influencer topics, each with a suggested interview guest.",
        "",
        "---",
        "",
    ]

    for pitch in pitches:
        format_label = pitch.get("guest_format_label", "Interview")
        guest_note = ""
        source_line = f"- **Source:** {pitch.get('source_name', '')} — {pitch['url']}" if pitch.get("url") else f"- **Source:** {pitch.get('source_name', 'Evergreen pitch')}"
        lines.extend(
            [
                f"## {pitch['rank']}. {pitch['headline']}",
                "",
                f"- **Kind:** {'Evergreen' if pitch.get('evergreen') else 'Timely'}",
                f"- **Type:** {pitch['pitch_type_label']}",
                f"- **Interview format:** {format_label}",
                f"- **Score:** {pitch['score']}",
                f"- **Angle:** {pitch['angle']}",
                f"- **Localize:** {pitch['localize']}",
                f"- **Why now:** {pitch['why_now']}",
                f"- **Interview:** {pitch['guest_name']}{guest_note} ({pitch['guest_role']})",
                f"- **Question / hook:** {pitch['guest_hook']}",
                f"- **Outreach:** {pitch['guest_outreach']}",
                source_line,
                "",
            ]
        )

    output_path.write_text("\n".join(lines))
    return output_path


def write_daily_html(pitches: list[dict], run_date: date | None = None) -> Path:
    run_date = run_date or date.today()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = OUTPUT_DIR / f"{run_date.isoformat()}.html"

    updated = datetime.now().strftime("%I:%M %p").lstrip("0")
    date_label = run_date.strftime("%A, %B %d, %Y")

    cards = []
    for pitch in pitches:
        format_label = html.escape(pitch.get("guest_format_label", "Interview"))
        cards.append(
            f"""
            <article class="card type-{html.escape(pitch['pitch_type'])} format-{html.escape(pitch.get('guest_format', 'named'))}">
              <div class="card-top">
                <span class="rank">#{pitch['rank']}</span>
                <span class="badge">{html.escape(pitch['pitch_type_label'])}</span>
                <span class="format-badge">{format_label}</span>
                <span class="score">{pitch['score']} pts</span>
              </div>
              <h2>{html.escape(pitch['headline'])}</h2>
              <p class="summary">{html.escape(pitch.get('summary') or pitch['angle'])}</p>
              <dl>
                <div><dt>Angle</dt><dd>{html.escape(pitch['angle'])}</dd></div>
                <div><dt>Localize</dt><dd>{html.escape(pitch['localize'])}</dd></div>
                <div><dt>Why now</dt><dd>{html.escape(pitch['why_now'])}</dd></div>
                <div><dt>{format_label}</dt><dd><strong>{html.escape(pitch['guest_name'])}</strong> · {html.escape(pitch['guest_role'])}</dd></div>
                <div><dt>Question / hook</dt><dd>{html.escape(pitch['guest_hook'])}</dd></div>
                <div><dt>Outreach</dt><dd>{html.escape(pitch['guest_outreach'])}</dd></div>
              </dl>
              {f'<a class="source" href="{html.escape(pitch["url"])}" target="_blank" rel="noopener">Read source →</a>' if pitch.get("url") else ""}
            </article>
            """
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Story Desk — {html.escape(date_label)}</title>
  <style>
    :root {{
      --bg: #0f1115;
      --panel: #171a21;
      --text: #eef1f6;
      --muted: #9aa3b2;
      --accent: #e85d04;
      --dallas: #2d6a4f;
      --influencer: #7b2cbf;
      --culture: #1d4ed8;
      --border: #2a3140;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      padding: 2rem 1.25rem 1rem;
      max-width: 920px;
      margin: 0 auto;
      border-bottom: 1px solid var(--border);
    }}
    header h1 {{
      margin: 0 0 .35rem;
      font-size: 2rem;
      letter-spacing: -0.02em;
    }}
    header p {{ margin: .25rem 0; color: var(--muted); }}
    .meta {{ font-size: .95rem; }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 1.25rem;
      display: grid;
      gap: 1rem;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.1rem 1.2rem 1.2rem;
    }}
    .card-top {{
      display: flex;
      gap: .6rem;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: .6rem;
    }}
    .rank {{
      font-weight: 700;
      color: var(--accent);
      font-size: .95rem;
    }}
    .badge {{
      font-size: .78rem;
      text-transform: uppercase;
      letter-spacing: .04em;
      padding: .18rem .55rem;
      border-radius: 999px;
      background: #222836;
      color: #dbe4ff;
    }}
    .type-dallas_local .badge {{ background: rgba(45,106,79,.25); color: #b7e4c7; }}
    .type-influencer .badge {{ background: rgba(123,44,191,.22); color: #e0aaff; }}
    .type-culture_media .badge {{ background: rgba(29,78,216,.22); color: #bfdbfe; }}
    .format-badge {{
      font-size: .78rem;
      padding: .18rem .55rem;
      border-radius: 999px;
      background: #2b2233;
      color: #f5d0fe;
    }}
    .format-named .format-badge {{ background: rgba(232,93,4,.18); color: #ffd6a5; }}
    .format-event .format-badge {{ background: rgba(45,106,79,.25); color: #b7e4c7; }}
    .format-mots .format-badge {{ background: rgba(100,116,139,.25); color: #e2e8f0; }}
    .score {{
      margin-left: auto;
      color: var(--muted);
      font-size: .85rem;
    }}
    h2 {{
      margin: 0 0 .55rem;
      font-size: 1.25rem;
      line-height: 1.35;
    }}
    .summary {{ color: var(--muted); margin: 0 0 .85rem; }}
    dl {{
      display: grid;
      gap: .55rem;
      margin: 0 0 1rem;
    }}
    dl div {{
      display: grid;
      grid-template-columns: 110px 1fr;
      gap: .75rem;
    }}
    dt {{
      color: var(--muted);
      font-size: .82rem;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    dd {{ margin: 0; }}
    .source {{
      color: var(--accent);
      text-decoration: none;
      font-size: .95rem;
    }}
    .source:hover {{ text-decoration: underline; }}
    footer {{
      max-width: 920px;
      margin: 0 auto;
      padding: 0 1.25rem 2rem;
      color: var(--muted);
      font-size: .9rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Story Desk</h1>
    <p class="meta">{html.escape(date_label)} · Updated {html.escape(updated)}</p>
    <p>10 culture/media pitches — Dallas/DFW local &amp; influencer topics with interview guests.</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
  <footer>
    Refreshes daily at 3:00 PM Central (cloud). Open anytime — at 7 PM you still see today's list.
  </footer>
</body>
</html>
"""

    dated_path.write_text(page)
    LATEST_HTML.write_text(page)
    LATEST_JSON.write_text(
        json.dumps(
            {"date": run_date.isoformat(), "updated": updated, "pitches": pitches},
            indent=2,
        )
    )
    return LATEST_HTML


def write_daily_outputs(pitches: list[dict], run_date: date | None = None) -> dict[str, str]:
    run_date = run_date or date.today()
    md = write_daily_markdown(pitches, run_date)
    html_path = write_daily_html(pitches, run_date)
    return {"markdown_path": str(md), "html_path": str(html_path)}
