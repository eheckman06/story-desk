# Story Desk

Your daily culture/media pitch list for **Elizabeth Heckman's Fox Digital beat** — 7 timely + 3 evergreen pitches, refreshed **every day at 3:00 PM Central**, even when your Mac is asleep.

## Three ways to open it

### 1. Cursor tab (recommended in the app)

**Today's pitches:** open **Canvas → `story-desk`**

**Full database** (search stories, interview subjects, daily picks): open **Canvas → `story-desk-database`**

Or double-click: `open_desk.command` (pitches) · `open_database.command` (database browser)

### 2. Cloud website (works when your computer is off)

Push this repo to GitHub and enable **GitHub Pages → Source: GitHub Actions**.

Then bookmark:

```text
https://<your-github-username>.github.io/story-desk/
```

The cloud job runs at **3:00 PM Central** every day. If you open it at **7 PM**, you still see **today's 3 PM list** until tomorrow's refresh.

**One-time setup:**

```bash
cd ~/Projects/story-desk
gh repo create story-desk --public --source=. --push
# GitHub → Settings → Pages → Build and deployment → GitHub Actions
```

### 3. Local file (same Mac)

```text
~/Projects/story-desk/data/latest.html       — today's pitches
~/Projects/story-desk/data/database.html     — interactive database browser
```

Refresh the database view anytime:

```bash
python3 ~/Projects/story-desk/scripts/refresh_database.py
```

## What's in each run

- **7 timely pitches** from live RSS (Dallas culture, influencers, Fox, etc.)
- **3 evergreen pitches** that rotate — always pitchable Dallas/influencer ideas
- Each pitch: **named interview**, **attend event**, or **man-on-the-street** with specific location/questions

## Run manually

```bash
cd ~/Projects/story-desk
python3 run_daily.py
```

This updates:

- `data/latest.html` — browser digest
- `canvases/story-desk.canvas.tsx` — Cursor tab
- `site/index.html` — cloud deploy folder

## Schedule

| Where | When |
|-------|------|
| **Cloud (GitHub Actions)** | 3:00 PM Central daily — works if Mac is off |
| **Local (optional LaunchAgent)** | 3:00 PM if Mac is awake — backup only |

Local LaunchAgent is optional once GitHub Pages is enabled.

## Customize

- `config/themes.json` — scoring weights, pitch counts
- `config/sources.json` — RSS feeds
- `config/evergreen.json` — evergreen pitch bank
