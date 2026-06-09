#!/usr/bin/env python3
"""Embed database snapshot into the interactive Cursor Canvas tab."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from story_desk.db_queries import export_database

CANVAS_DIR = Path.home() / ".cursor/projects/Users-elizabeth-heckman-Projects-story-desk/canvases"
CANVAS_FILE = CANVAS_DIR / "story-desk-database.canvas.tsx"

HEADER = '''import {
  Button, Card, CardBody, CardHeader, CollapsibleSection, H1, H2, Link, Pill, Row, Select,
  Stack, Stat, Table, Text, TextInput, useCanvasState, useHostTheme,
} from "cursor/canvas";

type Story = {
  id: number;
  title: string;
  url: string;
  summary?: string;
  source_name: string;
  score: number;
  theme_hits?: string;
  angle?: string;
  why_now?: string;
};

type Subject = {
  id: number;
  name: string;
  role?: string;
  story_url?: string;
  story_title?: string;
  hook?: string;
  contact_hint?: string;
  score: number;
  theme_hits?: string;
};

type Pick = {
  id: number;
  pick_date: string;
  pick_type: string;
  rank_num: number;
  title: string;
  detail?: string;
  score: number;
  source_url?: string;
};

type DbPayload = {
  exported_at: string;
  stats: {
    stories: number;
    subjects: number;
    picks: number;
    pick_dates: string[];
  };
  stories: Story[];
  subjects: Subject[];
  picks: Pick[];
};

const DB: DbPayload = '''

FOOTER = '''

type TabId = "stories" | "subjects" | "picks";

function includesQuery(haystack: string, q: string): boolean {
  if (!q.trim()) return true;
  return haystack.toLowerCase().includes(q.trim().toLowerCase());
}

function StoryTable({ rows }: { rows: Story[] }) {
  return (
    <Table
      headers={["Score", "Title", "Source", "Themes"]}
      columnAlign={["right", "left", "left", "left"]}
      striped
      stickyHeader
      emptyMessage="No stories match your filters."
      rows={rows.slice(0, 80).map((row) => [
        <Text weight="semibold" tone="primary">{row.score}</Text>,
        <Stack gap={4}>
          <Link href={row.url}>{row.title}</Link>
          {row.angle ? <Text size="small" tone="secondary">Angle: {row.angle}</Text> : null}
          {row.why_now ? <Text size="small" tone="secondary">Why now: {row.why_now}</Text> : null}
        </Stack>,
        <Text size="small">{row.source_name}</Text>,
        <Text size="small" tone="secondary">{row.theme_hits || "—"}</Text>,
      ])}
    />
  );
}

function SubjectTable({ rows }: { rows: Subject[] }) {
  return (
    <Table
      headers={["Score", "Name", "Role", "Hook"]}
      columnAlign={["right", "left", "left", "left"]}
      striped
      stickyHeader
      emptyMessage="No interview subjects match your filters."
      rows={rows.slice(0, 80).map((row) => [
        <Text weight="semibold" tone="primary">{row.score}</Text>,
        <Stack gap={4}>
          <Text weight="semibold">{row.name}</Text>
          {row.story_url ? <Link href={row.story_url}>Source story</Link> : null}
          {row.contact_hint ? <Text size="small" tone="secondary">Outreach: {row.contact_hint}</Text> : null}
        </Stack>,
        <Text size="small">{row.role || "—"}</Text>,
        <Text size="small" tone="secondary">{row.hook || row.story_title || "—"}</Text>,
      ])}
    />
  );
}

function PickTable({ rows }: { rows: Pick[] }) {
  return (
    <Table
      headers={["Date", "Rank", "Title", "Detail", "Score"]}
      columnAlign={["left", "right", "left", "left", "right"]}
      striped
      stickyHeader
      emptyMessage="No daily picks match your filters."
      rows={rows.slice(0, 80).map((row) => [
        <Text size="small">{row.pick_date}</Text>,
        <Text size="small">#{row.rank_num}</Text>,
        <Stack gap={4}>
          {row.source_url ? <Link href={row.source_url}>{row.title}</Link> : <Text>{row.title}</Text>}
          <Pill tone="neutral" size="sm">{row.pick_type}</Pill>
        </Stack>,
        <Text size="small" tone="secondary">{row.detail || "—"}</Text>,
        <Text weight="semibold" tone="primary">{row.score}</Text>,
      ])}
    />
  );
}

export default function StoryDeskDatabaseCanvas() {
  const theme = useHostTheme();
  const [tab, setTab] = useCanvasState<TabId>("tab", "stories");
  const [query, setQuery] = useCanvasState("query", "");
  const [minScore, setMinScore] = useCanvasState("minScore", "0");
  const [pickDate, setPickDate] = useCanvasState("pickDate", "all");

  const min = Number(minScore) || 0;

  const stories = DB.stories.filter(
    (row) =>
      row.score >= min &&
      includesQuery(
        [row.title, row.summary, row.source_name, row.theme_hits, row.angle].join(" "),
        query,
      ),
  );

  const subjects = DB.subjects.filter(
    (row) =>
      row.score >= min &&
      includesQuery(
        [row.name, row.role, row.story_title, row.hook, row.theme_hits, row.contact_hint].join(" "),
        query,
      ),
  );

  const picks = DB.picks.filter((row) => {
    if (pickDate !== "all" && row.pick_date !== pickDate) return false;
    if (row.score < min) return false;
    return includesQuery([row.title, row.detail, row.pick_type].join(" "), query);
  });

  const activeCount =
    tab === "stories" ? stories.length : tab === "subjects" ? subjects.length : picks.length;

  const dateOptions = [
    { value: "all", label: "All pick dates" },
    ...DB.stats.pick_dates.map((d) => ({ value: d, label: d })),
  ];

  return (
    <Stack gap={16} style={{ padding: 20, maxWidth: 980, color: theme.foreground }}>
      <Stack gap={6}>
        <H1>Story Desk Database</H1>
        <Text style={{ color: theme.descriptionForeground }}>
          {DB.stats.stories} stories · {DB.stats.subjects} interview subjects · {DB.stats.picks} daily picks
        </Text>
        <Text style={{ color: theme.descriptionForeground }}>
          Exported {DB.exported_at} · Search and filter below
        </Text>
      </Stack>

      <Row gap={12} wrap>
        <Stat label="Stories" value={String(DB.stats.stories)} />
        <Stat label="Subjects" value={String(DB.stats.subjects)} />
        <Stat label="Daily picks" value={String(DB.stats.picks)} />
        <Stat label="Showing" value={String(activeCount)} />
      </Row>

      <Card variant="outline">
        <CardBody>
          <Stack gap={10}>
            <Row gap={8} wrap align="center">
              <Button variant={tab === "stories" ? "primary" : "secondary"} onClick={() => setTab("stories")}>
                Stories
              </Button>
              <Button variant={tab === "subjects" ? "primary" : "secondary"} onClick={() => setTab("subjects")}>
                Interview subjects
              </Button>
              <Button variant={tab === "picks" ? "primary" : "secondary"} onClick={() => setTab("picks")}>
                Daily picks
              </Button>
            </Row>
            <Row gap={10} wrap align="center">
              <TextInput
                type="search"
                value={query}
                onChange={setQuery}
                placeholder="Search titles, names, themes…"
                style={{ flex: 1, minWidth: 220 }}
              />
              <Select
                value={minScore}
                onChange={setMinScore}
                options={[
                  { value: "0", label: "Any score" },
                  { value: "50", label: "Score 50+" },
                  { value: "70", label: "Score 70+" },
                  { value: "85", label: "Score 85+" },
                ]}
              />
              {tab === "picks" ? (
                <Select value={pickDate} onChange={setPickDate} options={dateOptions} />
              ) : null}
            </Row>
          </Stack>
        </CardBody>
      </Card>

      {tab === "stories" ? (
        <Stack gap={8}>
          <H2>Stories</H2>
          <StoryTable rows={stories} />
          {stories.length > 80 ? (
            <Text size="small" tone="secondary">Showing top 80 of {stories.length} matches.</Text>
          ) : null}
        </Stack>
      ) : null}

      {tab === "subjects" ? (
        <Stack gap={8}>
          <H2>Interview subjects</H2>
          <SubjectTable rows={subjects} />
          {subjects.length > 80 ? (
            <Text size="small" tone="secondary">Showing top 80 of {subjects.length} matches.</Text>
          ) : null}
        </Stack>
      ) : null}

      {tab === "picks" ? (
        <Stack gap={8}>
          <H2>Daily picks</H2>
          <PickTable rows={picks} />
          {picks.length > 80 ? (
            <Text size="small" tone="secondary">Showing top 80 of {picks.length} matches.</Text>
          ) : null}
        </Stack>
      ) : null}
    </Stack>
  );
}
'''


def main() -> None:
    payload = export_database()
    CANVAS_DIR.mkdir(parents=True, exist_ok=True)
    CANVAS_FILE.write_text(HEADER + json.dumps(payload, indent=2) + ";" + FOOTER)
    print(f"Database canvas updated: {CANVAS_FILE}")


if __name__ == "__main__":
    main()
