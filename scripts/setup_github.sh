#!/usr/bin/env bash
# One-time cloud setup: GitHub repo + Pages + first deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v gh >/dev/null 2>&1; then
  echo "Installing GitHub CLI to ~/.local/bin/gh ..."
  ARCH=$(uname -m)
  case "$ARCH" in arm64) GH_ARCH=arm64;; *) GH_ARCH=amd64;; esac
  GH_VERSION=2.63.2
  curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_macOS_${GH_ARCH}.zip" -o /tmp/gh.zip
  unzip -qo /tmp/gh.zip -d /tmp/gh-extract
  install -m 755 "/tmp/gh-extract/gh_${GH_VERSION}_macOS_${GH_ARCH}/bin/gh" "$HOME/.local/bin/gh"
fi

if ! gh auth status >/dev/null 2>&1; then
  echo ""
  echo "Sign in to GitHub (browser opens — takes ~30 seconds):"
  gh auth login --hostname github.com --git-protocol https --web
fi

cd "$ROOT"

if ! git remote get-url origin >/dev/null 2>&1; then
  gh repo create story-desk --public --source=. --remote=origin --push
else
  git push -u origin main
fi

# Enable GitHub Pages via Actions (required for daily.yml deploy)
gh api "repos/{owner}/{repo}/pages" \
  -X POST \
  -f build_type=workflow \
  -f source[branch]=main \
  -f source[path]=/ 2>/dev/null \
  || gh api "repos/{owner}/{repo}/pages" \
    -X PUT \
    -f build_type=workflow

echo ""
echo "Triggering first cloud build ..."
gh workflow run daily.yml
sleep 3
gh run list --workflow=daily.yml --limit 1

USER=$(gh api user -q .login)
echo ""
echo "Done. Bookmark your story desk:"
echo "  https://${USER}.github.io/story-desk/"
echo ""
echo "Updates daily at 3:00 PM Central, even when your Mac is off."
