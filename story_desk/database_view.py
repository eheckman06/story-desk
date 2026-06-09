"""Interactive HTML browser for the story desk database."""

from __future__ import annotations

import html
import json
from pathlib import Path

from story_desk.db_queries import export_database

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "database.html"


def write_database_html() -> Path:
    payload = export_database()
    data_json = json.dumps(payload)
    stats = payload["stats"]

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Story Desk Database</title>
  <style>
    :root {{
      --bg: #0f1117;
      --panel: #171a22;
      --border: #2a2f3a;
      --text: #e8eaed;
      --muted: #9aa3b2;
      --accent: #6ea8fe;
      --success: #3dd68c;
      --warning: #f5c451;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; }}
    h1 {{ margin: 0 0 6px; font-size: 1.75rem; }}
    .sub {{ color: var(--muted); margin-bottom: 20px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    .stat .n {{ font-size: 1.4rem; font-weight: 600; }}
    .stat .l {{ color: var(--muted); font-size: 0.85rem; }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 16px;
    }}
    .tabs {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .tab, .filter-btn {{
      background: var(--panel);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 6px;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 0.9rem;
    }}
    .tab.active, .filter-btn.active {{ border-color: var(--accent); color: var(--accent); }}
    input, select {{
      background: var(--panel);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 0.9rem;
      min-width: 180px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(110, 168, 254, 0.06); }}
    .score {{ color: var(--success); font-weight: 600; white-space: nowrap; }}
    .muted {{ color: var(--muted); font-size: 0.85rem; }}
    a {{ color: var(--accent); }}
    .detail-row td {{ background: #12151c; padding-top: 0; }}
    .detail {{
      padding: 0 12px 12px;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .empty {{ padding: 24px; text-align: center; color: var(--muted); }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 0.75rem;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Story Desk Database</h1>
    <p class="sub">Browse scored stories, interview subjects, and daily picks · Exported {html.escape(payload["exported_at"])}</p>

    <div class="stats">
      <div class="stat"><div class="n">{stats["stories"]}</div><div class="l">Stories</div></div>
      <div class="stat"><div class="n">{stats["subjects"]}</div><div class="l">Interview subjects</div></div>
      <div class="stat"><div class="n">{stats["picks"]}</div><div class="l">Daily picks</div></div>
      <div class="stat"><div class="n">{len(stats["pick_dates"])}</div><div class="l">Pick days</div></div>
    </div>

    <div class="toolbar">
      <div class="tabs" id="tabs"></div>
      <input type="search" id="search" placeholder="Search titles, names, themes…">
      <select id="minScore">
        <option value="0">Any score</option>
        <option value="50">Score 50+</option>
        <option value="70">Score 70+</option>
        <option value="85">Score 85+</option>
      </select>
      <select id="pickDate" style="display:none"></select>
    </div>

    <div id="tableWrap"></div>
  </div>

  <script>
    const DB = {data_json};

    const state = {{
      tab: "stories",
      q: "",
      minScore: 0,
      pickDate: "all",
      openId: null,
    }};

    const tabs = [
      {{ id: "stories", label: "Stories" }},
      {{ id: "subjects", label: "Interview subjects" }},
      {{ id: "picks", label: "Daily picks" }},
    ];

    function esc(s) {{
      return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    }}

    function matchQ(row, fields) {{
      if (!state.q) return true;
      const hay = fields.map(f => row[f] || "").join(" ").toLowerCase();
      return hay.includes(state.q.toLowerCase());
    }}

    function renderTabs() {{
      document.getElementById("tabs").innerHTML = tabs.map(t =>
        `<button class="tab ${{t.id === state.tab ? "active" : ""}}" data-tab="${{t.id}}">${{t.label}}</button>`
      ).join("");
    }}

    function renderPickDates() {{
      const sel = document.getElementById("pickDate");
      const show = state.tab === "picks";
      sel.style.display = show ? "inline-block" : "none";
      if (!show) return;
      const opts = ['<option value="all">All dates</option>'].concat(
        (DB.stats.pick_dates || []).map(d => `<option value="${{d}}">${{d}}</option>`)
      );
      sel.innerHTML = opts.join("");
      sel.value = state.pickDate;
    }}

    function storyRows() {{
      return DB.stories.filter(r => r.score >= state.minScore && matchQ(r, ["title","summary","source_name","theme_hits","angle"]));
    }}

    function subjectRows() {{
      return DB.subjects.filter(r => r.score >= state.minScore && matchQ(r, ["name","role","story_title","hook","theme_hits","contact_hint"]));
    }}

    function pickRows() {{
      return DB.picks.filter(r => {{
        if (state.pickDate !== "all" && r.pick_date !== state.pickDate) return false;
        if (r.score < state.minScore) return false;
        return matchQ(r, ["title","detail","pick_type"]);
      }});
    }}

    function renderTable() {{
      const wrap = document.getElementById("tableWrap");
      let headers = [];
      let rows = [];

      if (state.tab === "stories") {{
        headers = ["Score", "Title", "Source", "Themes"];
        rows = storyRows();
        wrap.innerHTML = tableHtml(headers, rows.map(r => [
          `<span class="score">${{r.score}}</span>`,
          titleCell(r.id, r.title, r.url, [
            r.summary && `<div>${{esc(r.summary)}}</div>`,
            r.angle && `<div><strong>Angle:</strong> ${{esc(r.angle)}}</div>`,
            r.why_now && `<div><strong>Why now:</strong> ${{esc(r.why_now)}}</div>`,
            r.published_at && `<div class="muted">Published ${{esc(r.published_at)}}</div>`,
          ]),
          esc(r.source_name),
          `<span class="pill">${{esc(r.theme_hits || "—")}}</span>`,
        ]));
      }} else if (state.tab === "subjects") {{
        headers = ["Score", "Name", "Role", "Story"];
        rows = subjectRows();
        wrap.innerHTML = tableHtml(headers, rows.map(r => [
          `<span class="score">${{r.score}}</span>`,
          titleCell(r.id, r.name, r.story_url, [
            r.hook && `<div><strong>Hook:</strong> ${{esc(r.hook)}}</div>`,
            r.why_elizabeth && `<div><strong>Why you:</strong> ${{esc(r.why_elizabeth)}}</div>`,
            r.contact_hint && `<div><strong>Outreach:</strong> ${{esc(r.contact_hint)}}</div>`,
            r.theme_hits && `<div class="pill">${{esc(r.theme_hits)}}</div>`,
          ]),
          esc(r.role || "—"),
          r.story_title ? `<span class="muted">${{esc(r.story_title)}}</span>` : "—",
        ]));
      }} else {{
        headers = ["Date", "Rank", "Title", "Detail", "Score"];
        rows = pickRows();
        wrap.innerHTML = tableHtml(headers, rows.map(r => [
          esc(r.pick_date),
          `#${{r.rank_num}}`,
          titleCell(r.id, r.title, r.source_url, [
            r.detail && `<div>${{esc(r.detail)}}</div>`,
            r.pick_type && `<div class="pill">${{esc(r.pick_type)}}</div>`,
          ]),
          esc(r.detail || "—"),
          `<span class="score">${{r.score}}</span>`,
        ]));
      }}

      if (!rows.length) {{
        wrap.innerHTML = `<div class="empty">No matches — try a lower score filter or different search.</div>`;
      }}

      wrap.querySelectorAll("[data-toggle]").forEach(el => {{
        el.addEventListener("click", () => {{
          const id = el.getAttribute("data-toggle");
          state.openId = state.openId === id ? null : id;
          renderTable();
        }});
      }});
    }}

    function titleCell(id, label, url, detailParts) {{
      const link = url
        ? `<a href="${{esc(url)}}" target="_blank" rel="noopener">${{esc(label)}}</a>`
        : esc(label);
      const open = state.openId === String(id);
      const detail = detailParts.filter(Boolean).join("");
      if (!detail) return link;
      return `${{link}} <button class="filter-btn" data-toggle="${{id}}" style="margin-left:8px;padding:2px 8px;font-size:0.75rem">${{open ? "Hide" : "Details"}}</button>` +
        (open ? `<div class="detail">${{detail}}</div>` : "");
    }}

    function tableHtml(headers, bodyRows) {{
      const head = `<tr>${{headers.map(h => `<th>${{h}}</th>`).join("")}}</tr>`;
      const body = bodyRows.map(cells => `<tr><td>${{cells.join("</td><td>")}}</td></tr>`).join("");
      return `<table><thead>${{head}}</thead><tbody>${{body}}</tbody></table>`;
    }}

    document.getElementById("tabs").addEventListener("click", e => {{
      const tab = e.target.closest("[data-tab]");
      if (!tab) return;
      state.tab = tab.dataset.tab;
      state.openId = null;
      renderPickDates();
      renderTabs();
      renderTable();
    }});

    document.getElementById("search").addEventListener("input", e => {{
      state.q = e.target.value;
      renderTable();
    }});

    document.getElementById("minScore").addEventListener("change", e => {{
      state.minScore = Number(e.target.value);
      renderTable();
    }});

    document.getElementById("pickDate").addEventListener("change", e => {{
      state.pickDate = e.target.value;
      renderTable();
    }});

    renderTabs();
    renderPickDates();
    renderTable();
  </script>
</body>
</html>
"""
    OUTPUT.write_text(doc)
    return OUTPUT
