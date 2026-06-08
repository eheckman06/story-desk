#!/usr/bin/env python3
"""Embed latest pitches into the Cursor Canvas tab."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "data" / "latest.json"
CANVAS_DIR = Path.home() / ".cursor/projects/Users-elizabeth-heckman-Projects-story-desk/canvases"
CANVAS_FILE = CANVAS_DIR / "story-desk.canvas.tsx"

HEADER = '''import {
  Card, CardBody, CardHeader, CollapsibleSection, H1, H2, Link, Pill, Row, Stack, Text,
  useHostTheme,
} from "cursor/canvas";

type Pitch = {
  rank: number;
  pitch_type_label: string;
  headline: string;
  angle: string;
  why_now: string;
  localize: string;
  guest_format_label: string;
  guest_name: string;
  guest_role: string;
  guest_hook: string;
  guest_outreach: string;
  url?: string;
  evergreen?: boolean;
  source_kind?: string;
};

type DeskPayload = {
  date: string;
  updated: string;
  pitches: Pitch[];
};

const DESK: DeskPayload = '''

FOOTER = '''

function formatTone(label: string): "neutral" | "success" | "warning" | "danger" {
  if (label.includes("Named")) return "success";
  if (label.includes("Attend")) return "warning";
  return "neutral";
}

function PitchList({ title, pitches }: { title: string; pitches: Pitch[] }) {
  const theme = useHostTheme();
  if (pitches.length === 0) return null;
  return (
    <Stack gap={10}>
      <H2>{title}</H2>
      {pitches.map((pitch) => (
        <Card key={pitch.rank} variant="outline">
          <CardHeader
            trailing={
              <Row gap={6}>
                {pitch.evergreen ? (
                  <Pill tone="warning" size="sm">Evergreen</Pill>
                ) : (
                  <Pill tone="success" size="sm">Timely</Pill>
                )}
                <Pill tone={formatTone(pitch.guest_format_label)} size="sm">
                  {pitch.guest_format_label}
                </Pill>
              </Row>
            }
          >
            {`#${pitch.rank} · ${pitch.headline}`}
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Type: {pitch.pitch_type_label}</Text>
              <Text>Angle: {pitch.angle}</Text>
              <Text>Why now: {pitch.why_now}</Text>
              <Text>Localize: {pitch.localize}</Text>
              <CollapsibleSection
                title={`${pitch.guest_format_label}: ${pitch.guest_name}`}
                trailing={<Text size="small">{pitch.guest_role}</Text>}
                defaultOpen={pitch.rank <= 2}
              >
                <Stack gap={6}>
                  <Text>Hook: {pitch.guest_hook}</Text>
                  <Text>Outreach: {pitch.guest_outreach}</Text>
                  {pitch.url ? <Link href={pitch.url}>Source</Link> : null}
                </Stack>
              </CollapsibleSection>
            </Stack>
          </CardBody>
        </Card>
      ))}
    </Stack>
  );
}

export default function StoryDeskCanvas() {
  const theme = useHostTheme();
  const timely = DESK.pitches.filter((p) => p.source_kind !== "evergreen" && !p.evergreen);
  const evergreen = DESK.pitches.filter((p) => p.source_kind === "evergreen" || p.evergreen);

  return (
    <Stack gap={16} style={{ padding: 20, maxWidth: 920, color: theme.foreground }}>
      <Stack gap={6}>
        <H1>Story Desk</H1>
        <Text style={{ color: theme.descriptionForeground }}>
          {DESK.date} · Updated {DESK.updated} · Refreshes daily at 3:00 PM Central
        </Text>
        <Text style={{ color: theme.descriptionForeground }}>
          Open anytime — if you check at 7 PM, you still see today's 3 PM list until tomorrow.
        </Text>
      </Stack>
      <PitchList title="Today's timely picks" pitches={timely} />
      <PitchList title="Evergreen pitches" pitches={evergreen} />
    </Stack>
  );
}
'''


def main() -> None:
    if not LATEST.exists():
        raise SystemExit(f"Missing {LATEST} — run python3 run_daily.py first")

    payload = json.loads(LATEST.read_text())
    CANVAS_DIR.mkdir(parents=True, exist_ok=True)
    CANVAS_FILE.write_text(HEADER + json.dumps(payload, indent=2) + ";" + FOOTER)
    print(f"Canvas updated: {CANVAS_FILE}")


if __name__ == "__main__":
    main()
