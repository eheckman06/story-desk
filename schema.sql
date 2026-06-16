CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT,
    source_id TEXT,
    source_name TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    score REAL DEFAULT 0,
    theme_hits TEXT,
    angle TEXT,
    why_now TEXT
);

CREATE TABLE IF NOT EXISTS interview_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    story_url TEXT,
    story_title TEXT,
    hook TEXT,
    why_elizabeth TEXT,
    contact_hint TEXT,
    score REAL DEFAULT 0,
    theme_hits TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_date TEXT NOT NULL,
    pick_type TEXT NOT NULL,
    rank_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    detail TEXT,
    score REAL DEFAULT 0,
    source_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stories_score ON stories(score DESC);
CREATE INDEX IF NOT EXISTS idx_subjects_score ON interview_subjects(score DESC);
CREATE INDEX IF NOT EXISTS idx_daily_picks_date ON daily_picks(pick_date, pick_type);

CREATE TABLE IF NOT EXISTS article_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airtable_id TEXT NOT NULL UNIQUE,
    title TEXT,
    url TEXT,
    publish_date TEXT,
    views REAL,
    author TEXT,
    section TEXT,
    topic TEXT,
    raw_fields TEXT,
    synced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_article_performance_views ON article_performance(views DESC);
