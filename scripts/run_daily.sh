#!/bin/zsh
set -euo pipefail

PROJECT="/Users/elizabeth.heckman/Projects/story-desk"
LOG_DIR="$PROJECT/data/logs"
ENV_FILE="$PROJECT/data/.env"
mkdir -p "$LOG_DIR"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

cd "$PROJECT"
{
  echo "=== $(date) ==="
  /usr/bin/python3 run_daily.py
} >> "$LOG_DIR/scheduled.log" 2>&1
